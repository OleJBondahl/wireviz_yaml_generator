
#let harness_doc(
  title: "Document Title",
  version: "01",
  date: "",
  logo_path: none,
  font_family: "Times New Roman",
  body
) = {
  set page(
    margin: (top: 5cm, bottom: 2cm, left: 1.5cm, right: 1.5cm),
    header-ascent: 30%,
    header: grid(
      columns: (1fr, auto, 1fr),
      align: (left+bottom, center+bottom, right+bottom),
      if logo_path != none { image(logo_path, width: 3cm) } else { [] },
      text(size: 12pt, style: "italic")[#title],
      text(size: 10pt, style: "italic")[Version: #version \ Date: #date],
    ),
    numbering: "1 / 1",
  )
  show table: set table(stroke: 0.5pt + black)
  set text(size: 11pt, font: font_family)
  body
}
