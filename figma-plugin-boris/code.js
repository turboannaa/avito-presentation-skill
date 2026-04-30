// Alter Post Creator — Dynamic Template Selection
// Scans the real section at runtime so hardcoded IDs are never needed.

figma.showUI(__html__, { width: 420, height: 560, title: "Alter Post Creator" });

var TEMPLATE_SECTION_ID = '121948:355';

// ── Entry point ───────────────────────────────────────────────────────────────

figma.ui.onmessage = async function(msg) {
  if (msg.type !== 'create-cards') return;
  try {
    await createPost(msg.cover, msg.cards);
    figma.ui.postMessage({ type: 'success' });
  } catch (e) {
    console.error('Plugin error:', e);
    figma.ui.postMessage({ type: 'error', message: e.message || String(e) });
  }
};

// ── Core ──────────────────────────────────────────────────────────────────────

async function createPost(cover, cards) {

  // 1. Load fonts
  progress(10, 'Загружаю шрифты...');
  var fontList = [
    { family: 'Montserrat', style: 'Regular' },
    { family: 'Montserrat', style: 'Medium' },
    { family: 'Montserrat', style: 'SemiBold' },
    { family: 'Montserrat', style: 'Bold' },
    { family: 'Montserrat', style: 'Italic' },
    { family: 'Montserrat', style: 'Medium Italic' },
    { family: 'Montserrat', style: 'SemiBold Italic' },
  ];
  for (var fi = 0; fi < fontList.length; fi++) {
    try { await figma.loadFontAsync(fontList[fi]); } catch(e) {}
  }

  // 2. Find template section
  progress(20, 'Ищу шаблон...');
  var section = figma.getNodeById(TEMPLATE_SECTION_ID);
  if (!section) {
    throw new Error(
      'Шаблонная секция не найдена (ID ' + TEMPLATE_SECTION_ID + ').\n' +
      'Убедитесь, что файл с шаблоном открыт в Figma.'
    );
  }

  // 3. Build variant map: { '1': [frame, frame, ...], '2': [...], ... }
  //    Multiple frames can have the same name — those are our variants.
  progress(25, 'Читаю варианты...');
  var variantMap = buildVariantMap(section);

  var availableSlots = Object.keys(variantMap);
  if (availableSlots.length === 0) {
    throw new Error('В секции не найдено фреймов. Убедитесь, что секция содержит карточки.');
  }

  // 4. Decide placement position (below the section)
  var originX = section.x;
  var originY = section.y + section.height + 200;
  var CARD_W  = 1080;
  var GAP     = 36;

  // 5. For each card slot, pick the best variant and clone it
  progress(30, 'Выбираю и клонирую...');

  var cardNums = Object.keys(cards)
    .filter(function(n){ return n !== '1'; })
    .sort(function(a, b){ return parseInt(a) - parseInt(b); });

  var entries = []; // { clone, cardNum }

  // ── Cover (slot 0) ──
  var coverVariants = variantMap['1'] || [];
  if (coverVariants.length === 0) {
    throw new Error('Не найдено ни одного фрейма с именем "1" (обложка) в секции.');
  }
  var bestCover = pickCoverVariant(coverVariants, cover);
  var coverClone = bestCover.clone();
  coverClone.x = originX;
  coverClone.y = originY;
  figma.currentPage.appendChild(coverClone);
  entries.push({ clone: coverClone, cardNum: '1' });

  // ── Content cards ──
  for (var si = 0; si < cardNums.length; si++) {
    var cn = cardNums[si];
    progress(30 + Math.floor((si / cardNums.length) * 40), 'Карточка ' + cn + '...');

    var variants = variantMap[cn] || [];
    if (variants.length === 0) {
      console.warn('No template for card ' + cn + ', skipping.');
      continue;
    }

    var best = pickContentVariant(variants, cards[cn]);
    var c = best.clone();
    c.x = originX + (si + 1) * (CARD_W + GAP);
    c.y = originY;
    figma.currentPage.appendChild(c);
    entries.push({ clone: c, cardNum: cn });
  }

  if (entries.length === 0) {
    throw new Error('Не удалось создать ни одной карточки.');
  }

  // 6. Update texts
  progress(72, 'Обновляю тексты...');
  await updateCover(coverClone, cover);

  for (var ei = 1; ei < entries.length; ei++) {
    var entry = entries[ei];
    if (cards[entry.cardNum]) {
      updateContentCard(entry.clone, cards[entry.cardNum]);
    }
    progress(72 + Math.floor((ei / entries.length) * 22), 'Текст ' + entry.cardNum + '...');
  }

  // 7. Done
  var allClones = entries.map(function(e){ return e.clone; });
  figma.viewport.scrollAndZoomIntoView(allClones);
  figma.notify('✅ ' + entries.length + ' карточек создано — ' + (cover.psychName || 'Готово'));
}

// ── Build variant map ─────────────────────────────────────────────────────────
// Scan the section's direct children and group by frame name.
// e.g. { '1': [frameA, frameB, frameC], '2': [...], ... }

function buildVariantMap(section) {
  var map = {};
  var children = section.children || [];
  for (var i = 0; i < children.length; i++) {
    var child = children[i];
    if (child.type !== 'FRAME') continue;
    var name = child.name.trim();
    if (!map[name]) map[name] = [];
    map[name].push(child);
  }
  return map;
}

// ── Cover variant picker ──────────────────────────────────────────────────────
// Prefer a cover that has a sub-text slot if a quote is present.

function pickCoverVariant(variants, cover) {
  var hasQuote = !!(cover.quote && cover.quote.trim().length > 0);
  if (!hasQuote) return variants[Math.floor(Math.random() * variants.length)];

  // Look for a variant that has a text node named "текст" (the sub-quote slot)
  for (var i = 0; i < variants.length; i++) {
    var texts = getAllTexts(variants[i]);
    for (var j = 0; j < texts.length; j++) {
      if (texts[j].name === 'текст') return variants[i];
    }
  }
  return variants[0];
}

// ── Content variant picker ────────────────────────────────────────────────────
// Score each variant by how well it fits the text (length, quotes, paragraphs).

function pickContentVariant(variants, text) {
  if (variants.length === 1) return variants[0];

  var charCount = text ? text.length : 0;
  var hasQuote  = /[«»]/.test(text || '');
  var paraCount = text
    ? text.split(/\n{2,}/).filter(function(p){ return p.trim(); }).length
    : 1;
  if (paraCount < 1) paraCount = 1;

  var best = variants[0];
  var bestScore = -Infinity;

  for (var i = 0; i < variants.length; i++) {
    var v = variants[i];
    var score = 0;

    // Estimate text capacity by summing text-node bounding box heights
    var texts = getAllTexts(v);
    var estCap = 0;
    for (var j = 0; j < texts.length; j++) {
      var bb = texts[j].absoluteBoundingBox;
      if (bb) estCap += Math.floor((bb.height / 45) * 38); // ~38 chars/line at 45px
    }
    if (estCap >= charCount) {
      score += 10;
      score -= ((estCap - charCount) / Math.max(estCap, 1)) * 3;
    } else {
      score -= ((charCount - estCap) / 100) * 4;
    }

    // Quote matching: does the template already use «» in its text?
    var templateHasQuote = false;
    for (var k = 0; k < texts.length; k++) {
      if (/[«»]/.test(texts[k].characters || '')) { templateHasQuote = true; break; }
    }
    if (hasQuote && templateHasQuote) score += 4;
    if (!hasQuote && !templateHasQuote) score += 1;

    // Text slot count vs paragraph count
    score -= Math.abs(texts.length - paraCount) * 0.5;

    if (score > bestScore) { bestScore = score; best = v; }
  }
  return best;
}

// ── Cover updater ─────────────────────────────────────────────────────────────

async function updateCover(frame, cover) {
  var texts = getAllTexts(frame);

  // Title = biggest font size
  var titleNode = findMaxFontSize(texts);
  if (titleNode && cover.title) safeSetChars(titleNode, cover.title);

  // Psychologist name
  var psychKeywords = ['психолог', 'Alter', 'Гордеева', 'Филимонова', 'Кузнецова',
                       'Никифоров', 'психолог Alter'];
  var psychNode = null;
  outer:
  for (var i = 0; i < texts.length; i++) {
    for (var pk = 0; pk < psychKeywords.length; pk++) {
      if ((texts[i].characters || '').indexOf(psychKeywords[pk]) >= 0) {
        psychNode = texts[i]; break outer;
      }
    }
  }
  if (psychNode && cover.psychName) {
    safeSetChars(psychNode, cover.psychName + '\nпсихолог Alter');
  }

  // Hashtag
  for (var j = 0; j < texts.length; j++) {
    if ((texts[j].characters || '').charAt(0) === '#') {
      safeSetChars(texts[j], cover.hashtag || '#вопрос_к_психологу');
      break;
    }
  }

  // Sub-quote slot — a node named "текст" that isn't the title
  if (cover.quote) {
    for (var k = 0; k < texts.length; k++) {
      if (texts[k] !== titleNode && texts[k].name === 'текст') {
        safeSetChars(texts[k], cover.quote);
        break;
      }
    }
  }

  // Avatar
  if (cover.avatarUrl) {
    try {
      var img = await figma.createImageAsync(cover.avatarUrl);
      var avatarNode = findDescByName(frame, 'Ellipse 2675');
      if (avatarNode && avatarNode.type !== 'TEXT') {
        avatarNode.fills = [{ type: 'IMAGE', scaleMode: 'FILL', imageHash: img.hash }];
      }
    } catch(e) { console.warn('Avatar failed:', e.message); }
  }
}

// ── Content card updater ──────────────────────────────────────────────────────

function updateContentCard(frame, rawText) {
  if (!rawText) return;
  var texts = getAllTexts(frame);
  if (!texts.length) return;

  texts.sort(function(a, b) {
    var ay = (a.absoluteBoundingBox || {}).y || 0;
    var by = (b.absoluteBoundingBox || {}).y || 0;
    return ay - by;
  });

  var paras = rawText.split(/\n{2,}/).map(function(p){ return p.trim(); }).filter(Boolean);
  if (!paras.length) return;

  if (texts.length === 1) {
    safeSetChars(texts[0], rawText.trim());
    return;
  }

  var chunks = distribute(paras, texts.length);
  for (var i = 0; i < texts.length; i++) {
    if (chunks[i] && chunks[i].trim()) safeSetChars(texts[i], chunks[i]);
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function getAllTexts(node) {
  var out = [];
  function walk(n) {
    if (n.type === 'TEXT') out.push(n);
    if (n.children) for (var i = 0; i < n.children.length; i++) walk(n.children[i]);
  }
  walk(node);
  return out;
}

function findMaxFontSize(texts) {
  var best = null;
  for (var i = 0; i < texts.length; i++) {
    if (!best || texts[i].fontSize > best.fontSize) best = texts[i];
  }
  return best;
}

function findDescByName(node, name) {
  if (node.name === name) return node;
  if (node.children) {
    for (var i = 0; i < node.children.length; i++) {
      var f = findDescByName(node.children[i], name);
      if (f) return f;
    }
  }
  return null;
}

function safeSetChars(node, text) {
  try { node.characters = String(text); }
  catch(e) { console.warn('setChars failed on "' + node.name + '":', e.message); }
}

function distribute(paras, slots) {
  if (paras.length <= slots) {
    var r = [];
    for (var i = 0; i < slots; i++) r.push(paras[i] || '');
    return r;
  }
  var out = [];
  var perSlot = Math.ceil(paras.length / slots);
  for (var s = 0; s < slots; s++) {
    out.push(paras.slice(s * perSlot, (s + 1) * perSlot).join('\n\n'));
  }
  return out;
}

function progress(pct, label) {
  figma.ui.postMessage({ type: 'progress', value: pct, label: label || '' });
}
