// パッケージをインポート
#import "@preview/equate:0.2.1": equate
#import "@preview/enja-bib:0.1.0": *
#import bib-setting-jsme: *

// フォントサイズ設定
#let font_size_body = 10pt
#let font_size_heading_1 = 20pt
#let font_size_heading_2 = 15pt
#let font_size_heading_3 = 13pt
#let font_size_heading_4 = 12pt
#let font_size_heading_5 = 11pt
#let font_size_heading_6 = 10pt
#let font_size_mono = 9pt

// 現在の日付設定
#let nowdate = {
  [#datetime.today().year()年#datetime.today().month()月#datetime.today().day()日]
}

// 日本語コード設定
#let cjkre = regex(
  "([\u3000-\u303F\u3040-\u30FF\u31F0-\u31FF\u3200-\u9FFF\uFF00-\uFFEF][　！”＃＄％＆’（）*+，−．／：；＜＝＞？＠［＼］＾＿｀｛｜｝〜、。￥・]*)[ ]+([\u3000-\u303F\u3040-\u30FF\u31F0-\u31FF\u3200-\u9FFF\uFF00-\uFFEF])[ ]*",
)

#let a4_ame_common_init(
  font_heading,
  font_body,
  font_latex,
  font_math,
  font_mono,
  body,
) = {
  // 日本語を設定
  set text(lang: "ja")
  // ページサイズを設定
  set page(
    paper: "a4",
    margin: (left: 20mm, right: 20mm, top: 20mm, bottom: 20mm),
    numbering: "1",
    number-align: center,
  )

  // 標準フォントを設定
  set text(font: font_body, size: font_size_body, cjk-latin-spacing: auto)

  // 行間を設定
  set par(leading: 0.8em)
  set par(spacing: 1.5em)

  // 数式フォントを設定
  show math.equation: set text(font: font_math)

  // コアカラー
  let darkest_purple = rgb("#460073")
  let dark_purple = rgb("#7500C0")
  let core_purple = rgb("#A100FF")
  let light_purple = rgb("#C2A3FF")
  let lightest_purple = rgb("#E6DCFF")
  let link_text_purple = rgb("#8550D0")

  // リンクのスタイル設定
  show link: it => {
    set text(fill: link_text_purple)
    underline(it)
  }

  // 見出しを設定
  show heading: it => [
    #let font_size = if (it.level == 1) {
      font_size_heading_1
    } else if (it.level == 2) {
      font_size_heading_2
    } else if (it.level == 3) {
      font_size_heading_3
    } else if (it.level == 4) {
      font_size_heading_4
    } else if (it.level == 5) {
      font_size_heading_5
    } else {
      font_size_heading_6
    }

    #set par(first-line-indent: 0em)
    #v(font_size)

    #set text(font: font_heading, weight: "bold", size: font_size)

    #let rule_thickness = 1.2pt
    #let rule_gap = 0.5em
    #let after_rule_gap = 0.5em

    // === レベル1だけ：中央揃え＋フル幅の「下線」風ルール ===
    #if it.level == 1 [
      #box(
        width: 100%,
        inset: (bottom: rule_gap),
        stroke: (bottom: (paint: dark_purple, thickness: rule_thickness)),
      )[
        #if counter(heading).display() != "0" and it.numbering != none {
          context counter(heading).display(it.numbering)
          h(font_size_body)
        }
        #align(center)[#it.body]
      ]
      #v(after_rule_gap)

      // === レベル2：左ボーダー＋薄い背景色（モダン・リッチ） ===
    ] else if it.level == 2 [
      #box(
        width: 100%,
        // 既存の余白感を壊さない程度に内側のパディングを設定
        inset: (left: 0.8em, top: 0.5em, bottom: 0.5em, right: 0.5em),
        fill: rgb("#F9F6FF"), // 非常に薄く上品な紫背景
        stroke: (left: (paint: core_purple, thickness: 4pt)), // 左にしっかりとしたアクセントライン
        radius: (right: 4pt), // 右側のみ角丸にして柔らかさを出す
      )[
        #if counter(heading).display() != "0" and it.numbering != none {
          context counter(heading).display(it.numbering)
          h(font_size_body)
        }
        #it.body
      ]
      #v(0.3em)

      // === レベル3：階層を明確にするための繊細な下線 ===
    ] else if it.level == 3 [
      #box(
        width: 100%,
        inset: (bottom: 0.3em),
        stroke: (bottom: (paint: light_purple, thickness: 0.5pt)),
      )[
        #if counter(heading).display() != "0" and it.numbering != none {
          context counter(heading).display(it.numbering)
          h(font_size_body)
        }
        #it.body
      ]
      #v(0.2em)

    ] else [
      // === それ以外のレベルは従来どおり ===
      #if counter(heading).display() != "0" and it.numbering != none {
        context counter(heading).display(it.numbering)
        h(font_size_body)
      }
      #it.body
    ]
  ]

  // 数式の設定
  show: equate.with(breakable: true, number-mode: "line")
  show math.equation.where(block: false): it => {
    let ghost = hide(text(font: "Adobe Blank", "\u{375}")) // 欧文ゴースト
    ghost
    it
    ghost
  }

  // 数式番号の設定
  show math.equation: set block(spacing: 2em)
  set math.equation(numbering: "(1)")
  show heading.where(level: 1): it => {
    counter(math.equation).update(0)
    counter(figure.where(kind: image)).update(0)
    counter(figure.where(kind: table)).update(0)
    counter(figure.where(kind: raw)).update(0)
    it
  }
  set math.equation(numbering: num => "(" + (str(counter(heading).get().at(0)) + "." + str(num)) + ")")

  // 図表番号の設定
  set figure(numbering: num => str(counter(heading).get().at(0)) + "." + str(num))
  set figure.caption(separator: [ ])

  // リストの設定 (作者: tinger)
  set list(indent: 1.5em)

  // 章の設定
  show figure.where(kind: "chapter"): it => {
    set par(first-line-indent: 0pt)
    set text(1.5em, font: font_heading, weight: "bold")

    align(left)[
      #if it.numbering != none {
        [第]
        context it.counter.display(it.numbering)
        [部]
        v(0.25em)
      }
      #text(1.25em, font: font_heading, weight: "bold", it.body)
    ]
  }

  show outline.entry: it => {
    set par(first-line-indent: 0em)
    if it.element.func() == figure {
      let res = link(
        it.element.location(),
        if it.element.numbering != none {
          linebreak()
          text(font: font_heading, size: 1em, weight: "bold", "第")
          text(font: font_heading, size: 1em, weight: "bold", numbering(it.element.numbering, ..it.element.counter.at(
            it.element.location(),
          )))
          text(font: font_heading, size: 1em, weight: "bold", "部")
          h(1em)
        }
          + text(font: font_heading, size: 1em, weight: "bold", it.element.body),
      )

      res += h(1fr)

      res += link(it.element.location(), it.page())
      text(font: font_heading, size: 1.2em, weight: "bold", res)
      v(0.5em)
    } else {
      it
      v(0.5em)
    }
  }

  show figure.where(kind: "chapter"): set text(black)

  // インラインコード (raw) のモダンなデザイン設定
  show raw.where(block: false): it => {
    box(
      fill: rgb("#F0F3F5"), // 少しクールでクリアなグレー
      stroke: 0.5pt + rgb("#D1D5DB"), // 繊細な枠線
      radius: 3pt,
      inset: (x: 4pt, y: 0pt),
      outset: (x: 0pt, y: 3pt),
      text(font: font_mono, size: font_size_mono, it),
    )
  }

  // コードブロック (raw) のモダンなデザイン設定
  show raw.where(block: true): it => {
    let lang = if it.lang != none { it.lang } else { "" }

    block(
      fill: rgb("#FAFBFC"), // GitHubライクな非常に明るく清潔な背景
      stroke: 1pt + rgb("#E1E4E8"), // しっかりとした細枠でリッチに
      radius: 6pt, // 少し大きめの角丸で今風のUIに寄せる
      inset: 12pt,
      width: 100%,
      above: 1.5em, // 前後の余白を少しだけ広げてゆったりと
      below: 1.5em,
      {
        set text(font: font_mono, size: font_size_mono)
        it
      },
    )
  }

  // 引用 (quote) のモダンなデザイン設定
  show quote: it => {
    block(
      fill: rgb("#F8F9FA"), // ニュートラルな明るいグレー
      stroke: (left: (paint: light_purple, thickness: 4pt)), // アクセントは紫
      radius: (right: 4pt),
      above: 1.5em,
      below: 1.5em,
      inset: (left: 1.2em, right: 1em, top: 0.8em, bottom: 0.8em),
      width: 100%,
      {
        set text(style: "italic", fill: rgb("#555555")) // 文字色を少し柔らかく
        it.body

        if it.attribution != none {
          v(0.5em)
          align(right)[— #text(weight: "bold", it.attribution)] // 引用元を太字で引き締める
        }
      },
    )
  }

  // Style table cells with a bottom border.
  show table.cell: it => {
    box(width: 100%, inset: it.inset, it)
  }

  // Style text within a table header.
  show table.header: it => {
    box(
      fill: dark_purple, // ヘッダーは少し濃い紫で引き締める
      width: 100%,
      align(center, {
        show text: t => text(weight: "bold", fill: white, t.body)
        it
      }),
    )
  }

  // 図キャプションの設定
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.caption: it => {
    v(0.5em)
    grid(
      columns: 2,
      align(top)[#it.supplement #context it.counter.display() #h(1em)], align(left)[#it.body],
    )
  }

  // 日本語文字間の改行を無効化
  show cjkre: it => it.text.match(cjkre).captures.sum()

  // 参考文献の設定
  show: bib-init

  // 作者: tinger
  let chapter = figure.with(
    kind: "chapter",
    numbering: none,
    supplement: [chapter],
    caption: "",
  )

  let chapters-and-headings = figure.where(kind: "chapter", outlined: true).or(heading.where(outlined: true))
  let chapter = chapter.with(numbering: "I")

  let jcls_appendix(body) = {
    counter(heading).update(0)
    counter("chapter").update(0)
    set heading(numbering: "A.1", outlined: false)
    show heading.where(level: 1): set heading(outlined: true)
    set math.equation(numbering: num => (
      "(" + (str(numbering("A", counter(heading).get().at(0))) + "." + str(num)) + ")"
    ))
    set figure(numbering: num => str(numbering("A", counter(heading).get().at(0))) + "." + str(num))
    body
  }

  let author-print(authors) = {
    let output-arguments = ()
    let tmp_list = ()
    for author in authors {
      let tmp = text(1.2em, [#author.name])
      let tmp2 = []
      if author.at("affiliation", default: []) != [] {
        if author.at("email", default: "") != "" {
          tmp2 = [#author.affiliation (#author.email)]
        } else {
          tmp2 = [#author.affiliation]
        }
      } else {
        if author.at("email", default: "") != "" {
          tmp2 = [#author.email]
        }
      }

      if tmp2 != [] {
        if tmp_list.contains(tmp2) {
          let num = 0
          for val in tmp_list {
            if val != tmp2 {
              num += 1
            } else {
              break
            }
          }
          tmp += super(str(num + 1))
        } else {
          tmp += footnote(tmp2)
          tmp_list.push(tmp2)
        }
      }
      output-arguments.push(tmp)
    }
    return output-arguments
  }

  let maketitle(
    title: [],
    abstract: [],
    keywords: (),
    authors: (),
    date: true,
    tableofcontents: false,
    body,
  ) = {
    pad(
      bottom: 4pt,
      top: 2cm,
      align(center)[
        #set text(font: (font_latex, font_body))
        #block(text(1.75em, title))
        #v(1em, weak: true)
      ],
    )
    pad(
      top: 1em,
      x: 2em,
      bottom: 1.5em,
      grid(
        align: center,
        columns: (1fr,) * calc.min(3, authors.len()),
        gutter: 1em,
        ..author-print(authors),
      ),
    )
    if date {
      v(-1em)
      align(center)[#text(1.2em, [#nowdate])]
    }
    if abstract != [] {
      pad(
        top: 1em,
        x: 3em,
        bottom: 0.4em,
        [
          #align(center)[
            #text(1.0em, emph(smallcaps[Abstract]), font: font_latex)
          ]
          #set par(justify: true)
          #set text(hyphenate: false)
          #abstract
        ],
      )
    } else {
      v(1.2cm, weak: true)
    }

    if tableofcontents {
      v(0.5cm)
      line(length: 100%, stroke: 0.5pt)
      outline(
        indent: auto,
        target: chapters-and-headings,
        title: [#h(-0.7em) 目次],
      )
      pagebreak()
    }
    body
  }

  let latex = {
    set text(font: font_latex)
    box(width: 2.55em, {
      [L]
      place(top, dx: 0.3em, text(size: 0.7em)[A])
      place(top, dx: 0.7em)[T]
      place(top, dx: 1.26em, dy: 0.22em)[E]
      place(top, dx: 1.8em)[X]
    })
  }

  let nonumber = <equate:revoke>

  body
}
