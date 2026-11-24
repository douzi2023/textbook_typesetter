// textbook.typ - 统编高中语文教科书出版级排版模板

#let c-text = rgb("#221e1f")
#let c-line = rgb("#221f1f")
#let c-brick = rgb("#af6b5c")

#let font-shusong = "FZShuSong-Z01"
#let font-yasong = "FZYaSong-M-GBK"
#let font-kaiti = "FZKai-Z03"
#let font-fangsong = "FZFangSong-Z02"
#let font-lanhei = "FZLanTingHei-DB-GBK"
#let font-dengxian = "FZZhongDengXian-Z07S"
#let font-rope = "RBNQWV+RopeSequenceNumberST-R"
#let font-neuxt = "NEU-XT"
#let font-times = "Times New Roman"

// 注释正文格式化：数字采用 Times New Roman，拼音采用 NEU-XT，汉字与标点保持方正书宋
#let fn-content(it) = {
  show regex("\d+"): set text(font: font-times)
  show regex("[a-zA-Z\u00C0-\u024F\u1E00-\u1EFF]+"): set text(font: font-neuxt)
  it
}

// 带圈序号映射（1~19使用Rope字体 a~s，20以上使用原字符）
#let circle-num(n) = {
  let chars = "abcdefghijklmnopqrs"
  if type(n) == int and n >= 1 and n <= 19 {
    text(font: font-rope, size: 9pt)[#chars.at(n - 1)]
  } else if type(n) == str and n.len() > 0 and "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲".contains(n) {
    let idx = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲".position(n)
    text(font: font-rope, size: 9pt)[#chars.at(idx)]
  } else {
    str(n)
  }
}

// 正文角标（7pt）
#let fn-mark(n) = {
  let sym = if type(n) == int {
    if n >= 1 and n <= 19 {
      "abcdefghijklmnopqrs".at(n - 1)
    } else if n >= 20 and n <= 23 {
      "tuvw".at(n - 20)
    } else if n >= 24 and n <= 29 {
      "@" + str(n - 20)
    } else if n >= 30 and n <= 39 {
      "#" + str(n - 30)
    } else {
      str(n)
    }
  } else if type(n) == str and n.len() > 0 and "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲".contains(n) {
    let idx = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲".position(n)
    "abcdefghijklmnopqrs".at(idx)
  } else {
    str(n)
  }
  text(font: (font-rope, font-shusong), size: 7pt, baseline: -4pt)[#sym]
}

// 格式化作者署名：二字名空一字（12pt），三字及以上紧凑排列
#let format-author(author) = {
  let clean = author.replace(" ", "").replace("　", "")
  if clean.clusters().len() == 2 {
    let c = clean.clusters()
    [#c.at(0)#h(12.0pt)#c.at(1)]
  } else {
    clean
  }
}

// 课文页面底座函数
#let textbook-doc(
  unit: "第二单元",
  book-title: "必修上册",
  start-page: 51,
  body
) = {
  let is-start-odd = calc.odd(start-page)
  let in-margin = if is-start-odd { 67.3pt } else { 156.0pt }
  let out-margin = if is-start-odd { 156.0pt } else { 67.3pt }

  set page(
    paper: "a4",
    margin: (inside: in-margin, outside: out-margin, top: 60.0pt, bottom: 50.0pt),
    header: none,
    footer: context {
      let p-index = here().page()
      let real-page = start-page + p-index - 1
      let is-odd = calc.odd(real-page)
      
      set text(fill: c-text)
      if is-odd {
        // 奇数页右下角: 靠右对齐到 535.3pt，距起点 67.3pt 为 409.3pt
        place(top + left, dx: 409.3pt, dy: -13.5pt)[
          #if unit != "" [#text(font: font-shusong, size: 9pt)[#unit]#h(11pt)]#text(font: font-dengxian, size: 10.5pt)[#real-page]
        ]
      } else {
        // 偶数页左下角: 靠左对齐到 60.0pt，距起点 156.0pt 为 -96.0pt
        place(top + left, dx: -96.0pt, dy: -13.5pt)[
          #text(font: font-dengxian, size: 10.5pt)[#real-page]#h(11pt)#text(font: font-shusong, size: 9pt)[语文]#h(7pt)#text(font: font-shusong, size: 9pt)[#book-title]
        ]
      }
    }
  )

  set text(font: font-shusong, size: 12.0pt, fill: c-text)
  set block(spacing: 0pt)

  body
}

// 课文首部标题组件（精准落位：序号y=58.9pt, 标题y=101.5pt, 作者y=145.6pt, 正文起点y=210.9pt）
#let lesson-header(
  num: none,
  title: "",
  title-fn: none,
  subtitle: none,
  author: none,
  is-odd: true
) = {
  // 大序号
  if num != none {
    let num-dx = if is-odd { 0pt } else { -88.7pt }
    place(top + left, dx: num-dx, dy: 58.9pt - 60.0pt)[
      #text(font: font-yasong, size: 24pt, fill: c-brick)[#str(num)]
    ]
  }

  // 主标题：y=101.5pt，居中于 372pt 栏内
  place(top + left, dx: 0pt, dy: 101.5pt - 60.0pt)[
    #block(width: 372.0pt)[
      #align(center)[
        #text(font: font-yasong, size: 21pt, fill: c-brick, tracking: 1.5pt)[#title]#if title-fn != none { fn-mark(title-fn) }
      ]
    ]
  ]

  // 副标题
  if subtitle != none {
    place(top + left, dx: 0pt, dy: 128.0pt - 60.0pt)[
      #block(width: 372.0pt)[
        #align(center)[
          #text(font: font-dengxian, size: 13pt, fill: c-text)[—— #subtitle]
        ]
      ]
    ]
  }

  // 作者：y=145.6pt
  if author != none {
    let dy-author = if subtitle != none { 152.0pt } else { 145.6pt }
    place(top + left, dx: 0pt, dy: dy-author - 60.0pt)[
      #block(width: 372.0pt)[
        #align(center)[
          #text(font: font-fangsong, size: 12pt, fill: c-text)[#format-author(author)]
        ]
      ]
    ]
  }

  // 占用高度直至 y=210.9pt 正文起点 (210.9 - 60.0 = 150.9pt)
  v(150.9pt)
}

// 正文单行组件（严格 21.0pt 行距，满行两端对齐到 372.0pt）
#let bl(it, indent: 0pt, is-last: false) = {
  block(height: 21.0pt, width: 372.0pt, inset: (left: indent))[
    #set par(justify: not is-last)
    #it
  ]
}

// 注释单行组件（严格 14.8pt 行距）
#let fn-line(sym: none, body: [], is-first: false, is-last: false) = {
  block(height: 14.8pt, width: 215.6pt)[
    #if is-first [
      #grid(columns: (13.5pt, 202.1pt), gutter: 0pt)[#box(width: 13.5pt, baseline: 0pt)[#sym]][#set par(justify: not is-last);#body]
    ] else [
      #box(width: 215.6pt)[
        #set par(justify: not is-last)
        #body
      ]
    ]
  ]
}

// 双栏页底注释组件（方案一：显式两栏网格平衡绑定）
#let footnote-section(left-lines, right-lines, is-odd: true) = {
  let line-offset-x = if is-odd { 0pt } else { -96.0pt }
  let container-offset-x = if is-odd { 0.1pt } else { -96.0pt }

  // 分割细线：长 144.0pt，粗 0.25pt
  place(top + left, dx: line-offset-x, dy: 0pt)[
    #line(length: 144.0pt, stroke: 0.25pt + c-line)
  ]

  // 注释双栏流式文本：距分割线 10.1pt
  place(top + left, dx: container-offset-x, dy: 10.1pt)[
    #block(width: 468.0pt)[
      #set text(font: font-shusong, size: 9.0pt, fill: c-text)
      #set block(spacing: 0pt)
      #set par(leading: 5.8pt)
      #grid(columns: (215.6pt, 215.6pt), gutter: 36.8pt)[
        #for l in left-lines [ #l ]
      ][
        #for l in right-lines [ #l ]
      ]
    ]
  ]
}

// 学习提示组件（正文下方约 41pt，虚线终点y=304.4pt，楷体正文y=333.6pt，绝对坐标固定）
#let hint-section(body, is-odd: false) = {
  v(41.2pt)
  let dx-header = if is-odd { -6.8pt } else { -95.5pt }
  let dx-body = if is-odd { 16.7pt } else { -72.0pt }

  move(dx: dx-header)[
    #block(width: 465.5pt)[
      #grid(
        columns: (22.7pt, 5.0pt, auto, 1fr),
        align: (left + horizon, left, left + horizon, left + horizon),
        image("images/textbook_hint_icon.png", width: 22.7pt, height: 22.7pt),
        none,
        text(font: font-lanhei, size: 14.0pt, fill: c-brick, tracking: 1.5pt)[学习提示],
        line(
          length: 100%,
          stroke: (
            paint: c-brick,
            thickness: 1.417pt,
            dash: (array: (0pt, 4.237pt), phase: 0pt),
            cap: "round"
          )
        )
      )
    ]
  ]
  v(13.8pt)
  move(dx: dx-body)[
    #block(width: 420.0pt)[
      #set text(font: font-kaiti, size: 12.0pt, fill: c-text)
      #set par(leading: 10.265625pt, first-line-indent: (amount: 24.0pt, all: true), justify: true)
      #body
    ]
  ]
}
