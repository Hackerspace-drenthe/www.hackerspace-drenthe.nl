---
title: "Nieuws"
menu: "Nieuws"
visible: true
template: blog
hero_image: "featured-nieuws.png"
content:
  items: '@self.children'
  order:
    by: date
    dir: desc
  pagination: false
process:
  markdown: true
  twig: false
---

<h2>Nieuws</h2><p>Laatste nieuws en activiteiten van Hackerspace Drenthe.</p>
