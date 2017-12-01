These are JS assets which don't work well with webpack/ES6 modules.

To bundle them up, run:

    cat modernizr.custom.js jquery.appear.js jquery.mousewheel.min.js  jquery-ui.min.js grid.js > vendor-all.js
