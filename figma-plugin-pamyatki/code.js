// Памятки по техникам — Figma Generator
// Generates 3 technique worksheets in Life Design Dashboard style

figma.skipInvisibleInstanceChildren = true;

// ── CONSTANTS ─────────────────────────────────────────────────────────────────
var W = 930;
var H = 1290;
var ML = 87;   // margin left
var CW = 756;  // content width (930 - 87*2)

var C_ACCENT  = { r: 102/255, g: 101/255, b: 221/255 }; // #6665DD
var C_BLACK   = { r: 47/255,  g: 47/255,  b: 47/255  }; // #2F2F2F
var C_WHITE   = { r: 1, g: 1, b: 1 };
var C_GRAY    = { r: 0.667, g: 0.667, b: 0.667 };       // #AAAAAA
var C_LINE    = { r: 0.82, g: 0.82, b: 0.82 };
var C_BGBOX   = { r: 0.97, g: 0.97, b: 0.97 };          // light gray box bg

// ── HELPERS ───────────────────────────────────────────────────────────────────

function rgb(r, g, b) { return { r: r/255, g: g/255, b: b/255 }; }

function makeFrame(name, x, y) {
  var f = figma.createFrame();
  f.name = name;
  f.resize(W, H);
  f.x = x;
  f.y = y;
  f.fills = [{ type: 'SOLID', color: C_WHITE }];
  f.clipsContent = true;
  figma.currentPage.appendChild(f);
  return f;
}

function addRect(parent, x, y, w, h, color, radius, opacity) {
  var r = figma.createRectangle();
  r.resize(w, h);
  r.x = x;
  r.y = y;
  r.cornerRadius = radius || 0;
  r.fills = [{ type: 'SOLID', color: color, opacity: opacity !== undefined ? opacity : 1 }];
  parent.appendChild(r);
  return r;
}

function addText(parent, content, x, y, w, fontSize, fontStyle, color, opacity) {
  var t = figma.createText();
  t.fontName = { family: 'Montserrat', style: fontStyle || 'Regular' };
  t.fontSize = fontSize || 18;
  t.characters = content;
  t.fills = [{ type: 'SOLID', color: color || C_BLACK, opacity: opacity !== undefined ? opacity : 1 }];
  if (w) {
    t.textAutoResize = 'HEIGHT';
    t.resize(w, t.height);
  }
  t.x = x;
  t.y = y;
  parent.appendChild(t);
  return t;
}

function addLine(parent, x, y, w) {
  var line = figma.createLine();
  line.x = x;
  line.y = y;
  line.resize(w, 0);
  line.strokes = [{ type: 'SOLID', color: C_LINE }];
  line.strokeWeight = 1;
  parent.appendChild(line);
  return line;
}

// Tilted accent rectangle (top-left, same as LDD)
function addAccentTag(frame, labelNum, totalPages) {
  var rect = addRect(frame, 78, 40, 130, 50, C_ACCENT, 12);
  rect.rotation = -2.53;
  // Number inside
  var numT = addText(frame, labelNum, 95, 45, 90, 28, 'SemiBold', C_WHITE);
  // Page counter bottom center
  var counter = addRect(frame, W/2 - 42, H - 82, 84, 36, C_BGBOX, 44);
  addText(frame, totalPages, W/2 - 28, H - 74, 56, 22, 'SemiBold', C_GRAY);
}

// Section pill badge (dark, same as LDD sub-headers)
function addBadge(frame, text, y) {
  var padding = 18;
  var tmpT = figma.createText();
  tmpT.fontName = { family: 'Montserrat', style: 'Medium' };
  tmpT.fontSize = 19;
  tmpT.characters = text;
  var tw = tmpT.width;
  tmpT.remove();

  var badgeW = tw + padding * 2;
  var badge = addRect(frame, ML, y, badgeW, 38, C_BLACK, 44);
  addText(frame, text, ML + padding, y + 8, tw + 4, 19, 'Medium', C_WHITE);
  return y + 38 + 18;
}

// Section header (italic, dimmed — same as "из Лекции 2 — ..." in LDD)
function addSectionRef(frame, text, y) {
  addText(frame, text, ML, y, CW, 24, 'SemiBold Italic', C_BLACK, 0.35);
  return y + 40;
}

// Body text (regular, black)
function addBody(frame, text, y, size, style, color) {
  var t = addText(frame, text, ML, y, CW, size || 19, style || 'Regular', color || C_BLACK);
  return y + t.height + 16;
}

// Writing lines
function addWriteLines(frame, y, count, gap) {
  gap = gap || 44;
  for (var i = 0; i < count; i++) {
    addLine(frame, ML, y + i * gap, CW);
  }
  return y + count * gap + 12;
}

// Simple 2-column table row
function addTableRow(frame, col1, col2, y, rowH, isHeader) {
  var col1W = 200;
  var col2W = CW - col1W - 2;
  var bg = isHeader ? C_BLACK : C_BGBOX;
  var textCol = isHeader ? C_WHITE : C_BLACK;
  var style = isHeader ? 'SemiBold' : 'Regular';

  addRect(frame, ML, y, col1W, rowH, bg, 0);
  addRect(frame, ML + col1W + 2, y, col2W, rowH, isHeader ? C_BLACK : { r: 0.95, g: 0.95, b: 0.95 }, 0);
  addText(frame, col1, ML + 10, y + 10, col1W - 16, 17, style, textCol);
  addText(frame, col2, ML + col1W + 12, y + 10, col2W - 16, 17, style, textCol);
  return y + rowH + 2;
}

// Numbered component box (for self-compassion 3 components)
function addComponentBox(frame, num, title, body, y) {
  var boxH = 100;
  addRect(frame, ML, y, 44, boxH, C_ACCENT, 8);
  addText(frame, num, ML + 13, y + 32, 20, 28, 'Bold', C_WHITE);
  addRect(frame, ML + 50, y, CW - 50, boxH, C_BGBOX, 8);
  addText(frame, title, ML + 64, y + 12, CW - 80, 18, 'SemiBold', C_BLACK);
  addText(frame, body, ML + 64, y + 38, CW - 80, 16, 'Regular', C_BLACK);
  return y + boxH + 10;
}

// Step box (3-step practice)
function addStepBox(frame, step, title, body, y) {
  addRect(frame, ML, y, CW, 2, C_ACCENT, 0);
  addText(frame, step + '. ' + title, ML, y + 10, CW, 19, 'SemiBold', C_ACCENT);
  var t = addText(frame, body, ML, y + 38, CW, 17, 'Regular', C_BLACK);
  return y + 38 + t.height + 20;
}

// Quote box
function addQuoteBox(frame, text, y) {
  addRect(frame, ML, y, 4, 80, C_ACCENT, 4);
  addText(frame, text, ML + 18, y + 10, CW - 20, 18, 'Medium Italic', C_BLACK);
  return y + 100;
}

// Horizon card for 10/10/10
function addHorizonCard(frame, number, timeLabel, question, y) {
  var cardH = 130;
  addRect(frame, ML, y, 56, cardH, C_ACCENT, 8);
  addText(frame, number, ML + 12, y + 18, 34, 32, 'Bold', C_WHITE);
  addRect(frame, ML + 62, y, CW - 62, cardH, C_BGBOX, 8);
  addText(frame, timeLabel, ML + 76, y + 14, CW - 90, 20, 'SemiBold', C_BLACK);
  addText(frame, question, ML + 76, y + 44, CW - 90, 16, 'Regular', C_BLACK);
  return y + cardH + 12;
}

// ── TECHNIQUE 1: САМОСОСТРАДАНИЕ ─────────────────────────────────────────────

function createTech1(baseX, baseY) {
  var frames = [];
  var y;

  // ── Page 1: Cover + Что это и зачем ──
  var f1 = makeFrame('Самосострадание 1/4', baseX, baseY);
  addAccentTag(f1, '01', '1/4');
  addText(f1, 'Практика самосострадания\nпри неудачах', ML, 120, CW, 42, 'Bold', C_BLACK);
  y = 250;
  addText(f1, 'Снизить самокритику и поддержать себя\nв момент ошибки или провала', ML, y, CW, 26, 'SemiBold Italic', C_BLACK, 0.38);
  y += 90;
  addLine(f1, ML, y, CW);
  y += 24;

  y = addBadge(f1, 'Что это и зачем', y);
  y = addBody(f1,
    'Самосострадание — это не жалость к себе и не отмазка от ответственности. Это способность отнестись к себе так же, как вы отнеслись бы к близкому другу в похожей ситуации: честно, но с теплом.',
    y, 18);
  y += 8;
  y = addBody(f1,
    'Кристин Нефф (Техасский университет) показала: люди, практикующие самосострадание, быстрее признают ошибки, легче берут ответственность и более настойчивы в достижении целей по сравнению с теми, кто мотивирует себя через самокритику. Жёсткость к себе блокирует поведение, а не мотивирует.',
    y, 18);
  y += 16;
  addLine(f1, ML, y, CW);
  frames.push(f1);

  // ── Page 2: Три компонента ──
  var f2 = makeFrame('Самосострадание 2/4', baseX + W + 40, baseY);
  addAccentTag(f2, '01', '2/4');
  y = 120;
  y = addBadge(f2, 'Три компонента (по Нефф)', y);

  y = addComponentBox(f2, '1', 'Доброта к себе',
    'Вместо осуждения — говорить себе то, что сказали бы другу. Не «я снова облажался», а «это было трудно, и я справился как мог».',
    y);
  y = addComponentBox(f2, '2', 'Общая человечность',
    'Напомнить себе: это испытывают все люди. Ошибаться, терпеть неудачи — это часть человеческого опыта, а не ваша особая «поломка».',
    y);
  y = addComponentBox(f2, '3', 'Осознанность',
    'Видеть боль или неудачу без преувеличения («всё пропало») и без подавления («нормально, всё ок»). Признавать: «Сейчас мне больно, и это реальность».',
    y);

  y += 16;
  addLine(f2, ML, y, CW);
  y += 24;
  y = addBadge(f2, 'Практика: 3 шага после неудачи', y);
  addText(f2, 'Когда что-то пошло не так — остановитесь и пройдите три шага. Это займёт около 5 минут.', ML, y, CW, 18, 'Regular', C_BLACK);
  frames.push(f2);

  // ── Page 3: 3 шага + проверочный вопрос ──
  var f3 = makeFrame('Самосострадание 3/4', baseX + (W + 40) * 2, baseY);
  addAccentTag(f3, '01', '3/4');
  y = 120;

  y = addStepBox(f3, 'Шаг 1', 'Признайте боль',
    'Скажите себе вслух или запишите: «Сейчас мне трудно / больно / стыдно. Это нормально — чувствовать это». Не оценивайте чувство, а просто назовите его.',
    y);
  y = addStepBox(f3, 'Шаг 2', 'Вспомните об общей человечности',
    'Скажите себе: «Я не один/одна в этом. Многие люди переживали то же самое. Это часть жизни, а не моя особая "поломка"».',
    y);
  y = addStepBox(f3, 'Шаг 3', 'Скажите себе то, что сказали бы другу',
    'Представьте, что ваш близкий друг оказался в точно такой же ситуации. Что бы вы ему сказали? Скажите это себе теми же словами. Можно написать письмо от лица друга к себе.',
    y);

  y += 10;
  addLine(f3, ML, y, CW);
  y += 24;
  y = addBadge(f3, 'Проверочный вопрос', y);
  y = addQuoteBox(f3, '«Если бы мой лучший друг сделал то же самое и чувствовал то же самое, что бы я ему сказал(а)?»', y);

  y += 8;
  addText(f3, 'Запишите здесь свои слова поддержки:', ML, y, CW, 18, 'SemiBold', C_BLACK);
  y += 36;
  y = addWriteLines(f3, y, 5, 42);
  frames.push(f3);

  // ── Page 4: Когда использовать + Важно помнить ──
  var f4 = makeFrame('Самосострадание 4/4', baseX + (W + 40) * 3, baseY);
  addAccentTag(f4, '01', '4/4');
  y = 120;

  y = addBadge(f4, 'Когда использовать эту технику', y);
  var whenItems = [
    '— после ошибки или провала (ситуации, которую вы воспринимаете как провал)',
    '— когда «внутренний критик» особенно громкий',
    '— после отката в изменениях (пропустил(а) неделю экспериментов, вернулся(ась) к старому паттерну)',
    '— когда стыдно за что-то сказанное или несделанное'
  ];
  for (var i = 0; i < whenItems.length; i++) {
    y = addBody(f4, whenItems[i], y, 18);
    y -= 6;
  }
  y += 20;
  addLine(f4, ML, y, CW);
  y += 24;

  y = addBadge(f4, 'Важно помнить', y);
  y = addBody(f4,
    'Самосострадание не означает отсутствие ответственности. После того как вы поддержали себя, можно честно разобраться, что произошло и что можно сделать иначе в следующий раз.',
    y, 18);
  y += 8;
  y = addQuoteBox(f4, 'Правило: сначала поддержка, потом анализ — а не наоборот.', y);

  y += 24;
  addLine(f4, ML, y, CW);
  y += 20;
  addText(f4, 'Источники: Нефф К. «Самосострадание». Нефф К., Гермер К. «Mindful Self-Compassion».', ML, y, CW, 15, 'Italic', C_GRAY);
  frames.push(f4);

  return frames;
}

// ── TECHNIQUE 2: 5 ПОЧЕМУ ────────────────────────────────────────────────────

function createTech2(baseX, baseY) {
  var frames = [];
  var y;

  // ── Page 1: Cover + теория ──
  var f1 = makeFrame('5 почему 1/4', baseX, baseY);
  addAccentTag(f1, '02', '1/4');
  addText(f1, 'Техника «5 почему»', ML, 120, CW, 42, 'Bold', C_BLACK);
  y = 220;
  addText(f1, 'Найти настоящую причину своих реакций,\nрешений и паттернов', ML, y, CW, 26, 'SemiBold Italic', C_BLACK, 0.38);
  y += 90;
  addLine(f1, ML, y, CW);
  y += 24;

  y = addBadge(f1, 'Что это и зачем', y);
  y = addBody(f1, '«5 почему» — метод, разработанный в компании Toyota для поиска корневых причин технических сбоев. Сакити Тоёда заметил: люди почти всегда останавливаются на первом удобном объяснении, а не на настоящей причине.', y, 18);
  y += 8;
  y = addBody(f1, 'В работе с собой это тоже применимо. Мы говорим «я прокрастинирую», но почему? «Потому что устал», но почему устал? Каждый уровень «почему» приближает нас к более глубокому пониманию источника поведения и наших потребностей.', y, 18);
  y += 16;
  addLine(f1, ML, y, CW);
  y += 24;

  y = addBadge(f1, 'Как работает', y);
  y = addBody(f1, 'Возьмите любую реакцию, решение или паттерн поведения, который хотите понять. Задайте вопрос «почему?» и к каждому ответу снова задайте вопрос «почему?». Повторите пять раз.', y, 18);
  y += 8;
  y = addBody(f1, 'Пять итераций — не жёсткое правило. Иногда хватает трёх, иногда нужно семь. Ориентир: вы добрались до финальной причины, когда ответ касается ценностей, страхов, глубоких убеждений или базовых потребностей.', y, 18);
  frames.push(f1);

  // ── Page 2: Пример ──
  var f2 = makeFrame('5 почему 2/4', baseX + (W + 40), baseY);
  addAccentTag(f2, '02', '2/4');
  y = 120;
  y = addBadge(f2, 'Пример', y);
  addText(f2, 'Ситуация: я снова не сдержал(а) обещание себе и не занялся(ась) спортом.', ML, y, CW, 18, 'Medium', C_BLACK);
  y += 44;

  var exampleRows = [
    ['Почему 1', 'Не было времени.'],
    ['Почему 2', 'Весь день занял рабочий аврал.'],
    ['Почему 3', 'Я не умею говорить «нет» новым задачам, даже когда план уже полный.'],
    ['Почему 4', 'Я боюсь, что если откажу, меня посчитают ненадёжным(ой) или эгоистичным(ой).'],
    ['Почему 5', 'Глубоко внутри я убеждён(а), что моя ценность зависит от того, насколько я полезен(а) другим.'],
    ['Глубинная причина', 'Убеждение «я ценен(а) только когда полезен(а)» — а не «не было времени».'],
  ];
  y = addTableRow(f2, 'Итерация', 'Ответ', y, 36, true);
  for (var i = 0; i < exampleRows.length; i++) {
    var rh = i === 4 || i === 5 ? 72 : 48;
    y = addTableRow(f2, exampleRows[i][0], exampleRows[i][1], y, rh, false);
  }
  y += 16;
  y = addBody(f2, 'Вывод: я приоритизирую полезность другим людям, а не заботу о себе. Хочу ли я быть таким человеком и дальше? (ответ зависит от иерархии ваших ценностей)', y, 17, 'Italic', C_GRAY);
  frames.push(f2);

  // ── Page 3: Ваша практика ──
  var f3 = makeFrame('5 почему 3/4', baseX + (W + 40) * 2, baseY);
  addAccentTag(f3, '02', '3/4');
  y = 120;
  y = addBadge(f3, 'Ваша практика', y);
  addText(f3, 'Выберите ситуацию, реакцию или паттерн, который хотите исследовать:', ML, y, CW, 18, 'Regular', C_BLACK);
  y += 36;
  y = addWriteLines(f3, y, 3, 40);
  y += 16;

  var practiceRows = [
    ['Ситуация / паттерн', ''],
    ['Почему 1', ''],
    ['Почему 2', ''],
    ['Почему 3', ''],
    ['Почему 4', ''],
    ['Почему 5', ''],
    ['Глубинная причина', ''],
  ];
  y = addTableRow(f3, 'Итерация', 'Почему это происходит / я так делаю?', y, 36, true);
  for (var j = 0; j < practiceRows.length; j++) {
    var rh2 = (j === 0 || j === 6) ? 72 : 56;
    y = addTableRow(f3, practiceRows[j][0], practiceRows[j][1], y, rh2, false);
  }
  y += 16;
  addText(f3, 'Что я хочу сделать с этим знанием?', ML, y, CW, 18, 'SemiBold', C_BLACK);
  y += 36;
  y = addWriteLines(f3, y, 3, 40);
  frames.push(f3);

  // ── Page 4: Что делать + рекомендации ──
  var f4 = makeFrame('5 почему 4/4', baseX + (W + 40) * 3, baseY);
  addAccentTag(f4, '02', '4/4');
  y = 120;

  y = addBadge(f4, 'Что делать с ответом', y);
  y = addBody(f4, 'Корневая причина — это не приговор. Это точка входа. Когда вы знаете глубинную причину паттерна, вы можете работать с ней, а не с симптомом.', y, 18);
  y += 20;
  addLine(f4, ML, y, CW);
  y += 24;

  y = addBadge(f4, 'Рекомендации', y);
  var recs = [
    '— отвечайте быстро: первый ответ часто честнее обдуманного',
    '— не оценивайте ответы в процессе, просто фиксируйте',
    '— техника хорошо работает в диалоге: партнёр задаёт «почему», вы отвечаете',
    '— признак глубинной причины: вы натолкнулись на ценности, страхи, убеждения о себе или базовые потребности (автономность, компетентность, связанность)'
  ];
  for (var k = 0; k < recs.length; k++) {
    y = addBody(f4, recs[k], y, 18);
    y -= 6;
  }
  y += 24;
  addLine(f4, ML, y, CW);
  y += 20;
  addText(f4, 'Источник: метод разработан Сакити Тоёдой (Toyota Production System). Адаптирован для психологической работы.', ML, y, CW, 15, 'Italic', C_GRAY);
  frames.push(f4);

  return frames;
}

// ── TECHNIQUE 3: 10/10/10 ────────────────────────────────────────────────────

function createTech3(baseX, baseY) {
  var frames = [];
  var y;

  // ── Page 1: Cover + теория ──
  var f1 = makeFrame('10-10-10 1/4', baseX, baseY);
  addAccentTag(f1, '03', '1/4');
  addText(f1, 'Техника принятия решений\n«10/10/10»', ML, 120, CW, 42, 'Bold', C_BLACK);
  y = 250;
  addText(f1, 'Принимать решения с учётом долгосрочных\nпоследствий и отличать сиюминутный страх\nот подлинных ценностей', ML, y, CW, 24, 'SemiBold Italic', C_BLACK, 0.38);
  y += 110;
  addLine(f1, ML, y, CW);
  y += 24;

  y = addBadge(f1, 'Что это и зачем', y);
  y = addBody(f1, 'Когда мы принимаем решения под давлением момента — стресса, страха, чужого ожидания или сильного желания — мы переоцениваем важность того, что происходит прямо сейчас, и недооцениваем то, что будет потом.', y, 18);
  y += 8;
  y = addBody(f1, 'Техника «10/10/10» разработана журналисткой Сьюзи Уэлч. Принцип: задать три временных вопроса о последствиях решения — через 10 минут, 10 месяцев и 10 лет. Это разрывает «тоннельное зрение» момента.', y, 18);
  y += 8;
  y = addBody(f1, 'Миметические желания почти всегда «горят» в перспективе 10 минут и «гаснут» в перспективе 10 месяцев. Подлинные, наоборот, остаются значимыми спустя годы — и эта техника помогает это увидеть.', y, 18);
  frames.push(f1);

  // ── Page 2: Три вопроса ──
  var f2 = makeFrame('10-10-10 2/4', baseX + (W + 40), baseY);
  addAccentTag(f2, '03', '2/4');
  y = 120;
  y = addBadge(f2, 'Три вопроса', y);

  y = addHorizonCard(f2, '1', 'Через 10 минут',
    'Как я буду себя чувствовать сразу после того, как приму это решение? Здесь работают эмоции момента: облегчение, страх, удовольствие, стыд.',
    y);
  y = addHorizonCard(f2, '2', 'Через 10 месяцев',
    'Как я буду себя чувствовать через 10 месяцев? Будет ли это решение всё ещё иметь значение?',
    y);
  y = addHorizonCard(f2, '3', 'Через 10 лет',
    'Как я буду себя чувствовать через 10 лет? Буду ли я рад(а), что принял(а) именно это решение? Этот горизонт выравнивает решение с долгосрочными ценностями.',
    y);
  frames.push(f2);

  // ── Page 3: Ваша практика ──
  var f3 = makeFrame('10-10-10 3/4', baseX + (W + 40) * 2, baseY);
  addAccentTag(f3, '03', '3/4');
  y = 120;
  y = addBadge(f3, 'Ваша практика', y);
  addText(f3, 'Напишите решение, которое нужно принять:', ML, y, CW, 18, 'Regular', C_BLACK);
  y += 36;
  y = addWriteLines(f3, y, 3, 40);
  y += 16;

  var horizonRows = [
    ['Через 10 минут', 'Как я буду себя чувствовать?', ''],
    ['Через 10 месяцев', 'Будет ли это иметь значение?', ''],
    ['Через 10 лет', 'Буду ли я рад(а) этому выбору?', ''],
  ];
  y = addTableRow(f3, 'Горизонт', 'Как я буду себя чувствовать? Что будет иметь значение?', y, 40, true);
  for (var i = 0; i < horizonRows.length; i++) {
    y = addTableRow(f3, horizonRows[i][0], horizonRows[i][1], y, 80, false);
  }
  y += 20;
  addText(f3, 'Что вы заметили? Посмотрите на картину целиком:', ML, y, CW, 18, 'SemiBold', C_BLACK);
  y += 36;
  addText(f3, 'В каком горизонте это решение самое важное?', ML, y, CW, 17, 'Italic', C_GRAY);
  y += 24;
  y = addWriteLines(f3, y, 2, 38);
  addText(f3, 'Что говорят ваши ценности?', ML, y, CW, 17, 'Italic', C_GRAY);
  y += 24;
  y = addWriteLines(f3, y, 2, 38);
  addText(f3, 'Какое решение вы принимаете?', ML, y, CW, 17, 'Italic', C_GRAY);
  y += 24;
  y = addWriteLines(f3, y, 2, 38);
  frames.push(f3);

  // ── Page 4: Когда полезна + Важно ──
  var f4 = makeFrame('10-10-10 4/4', baseX + (W + 40) * 3, baseY);
  addAccentTag(f4, '03', '4/4');
  y = 120;

  y = addBadge(f4, 'Когда особенно полезна эта техника', y);
  var whenItems = [
    '— когда решение принимается под давлением (дедлайн, чужое ожидание, страх упустить момент)',
    '— когда очень хочется что-то сделать прямо сейчас, но это кажется импульсивным',
    '— когда трудно понять, чего вы хотите на самом деле',
    '— для значимых решений: смена работы, переезд, окончание или начало отношений',
    '— для небольших, но повторяющихся: «снова сказать да, когда хочется сказать нет»'
  ];
  for (var j = 0; j < whenItems.length; j++) {
    y = addBody(f4, whenItems[j], y, 18);
    y -= 6;
  }
  y += 20;
  addLine(f4, ML, y, CW);
  y += 24;

  y = addBadge(f4, 'Важное уточнение', y);
  y = addBody(f4, 'Техника «10/10/10» не даёт «правильного» ответа — она даёт более полную картину последствий. Вы можете увидеть, что решение важно в трёх горизонтах сразу, или что оно горит только сейчас. Оба варианта — информация.', y, 18);
  y += 24;
  addLine(f4, ML, y, CW);
  y += 20;
  addText(f4, 'Источник: Уэлч С. «10/10/10: A Life-Transforming Idea». Simon & Schuster, 2009.', ML, y, CW, 15, 'Italic', C_GRAY);
  frames.push(f4);

  return frames;
}

// ── MAIN ──────────────────────────────────────────────────────────────────────

(async function() {
  // Load all fonts first
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

  var startX = 200;
  var startY = 200;
  var rowGap = H + 160;
  var colGap = W + 40;

  var t1 = createTech1(startX, startY);
  var t2 = createTech2(startX, startY + rowGap);
  var t3 = createTech3(startX, startY + rowGap * 2);

  var all = t1.concat(t2).concat(t3);
  figma.viewport.scrollAndZoomIntoView(all);
  figma.notify('✅ Готово — 12 страниц памяток созданы!');
  figma.closePlugin();
})();
