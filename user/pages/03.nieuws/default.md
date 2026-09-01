---
title: "Nieuws"
menu: "Nieuws"
visible: true
template: blog
content:
  items: '@self.children'
  order:
    by: date
    dir: desc
  pagination: true
  limit: 10
process:
  markdown: true
  twig: false
---

<h2>Nieuws</h2><p>Laatste nieuws en activiteiten van Hackerspace Drenthe.</p>
