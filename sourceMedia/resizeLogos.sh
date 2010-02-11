#!/bin/bash
convert -resize 1000x45 google_logo.gif ../static/img/google_logo.png
convert -resize 1000x45 nasa_logo.gif ../static/img/nasa_logo.png
convert -resize 1000x45 rhok_logo.gif ../static/img/rhok_logo.png
convert -resize 1000x45 wb_logo.png ../static/img/wb_logo.png
identify ../static/img/*_logo.png
