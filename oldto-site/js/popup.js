// Source: https://developers.google.com/maps/documentation/javascript/examples/overlay-popup
// Modernized to use ES6 classes.

/**
 * A customized popup on the map.
 * @param {!google.maps.LatLng} position
 * @param {!Element} content
 * @constructor
 * @extends {google.maps.OverlayView}
 */
export class Popup extends google.maps.OverlayView {
  constructor(position, content) {
    super(position, content);
    this.position = position;
    this.contentDiv = content;

    content.classList.add('popup-bubble-content');

    var pixelOffset = document.createElement('div');
    pixelOffset.classList.add('popup-bubble-anchor');
    pixelOffset.appendChild(this.contentDiv);

    this.anchor = document.createElement('div');
    this.anchor.classList.add('popup-tip-anchor');
    this.anchor.appendChild(pixelOffset);
  }

  /** Called when the popup is added to the map. */
  onAdd() {
    this.getPanes().floatPane.appendChild(this.anchor);
  }

  /** Called when the popup is removed from the map. */
  onRemove() {
    if (this.anchor.parentElement) {
      this.anchor.parentElement.removeChild(this.anchor);
    }
  }

  /** Called when the popup needs to draw itself. */
  draw() {
    const projection = this.getProjection();
    if (!projection) return;
    var divPosition = projection.fromLatLngToDivPixel(this.position);
    // Hide the popup when it is far out of view.
    var display =
        Math.abs(divPosition.x) < 4000 && Math.abs(divPosition.y) < 4000 ?
        'block' :
        'none';

    if (display === 'block') {
      this.anchor.style.left = divPosition.x + 'px';
      this.anchor.style.top = divPosition.y + 'px';
    }
    if (this.anchor.style.display !== display) {
      this.anchor.style.display = display;
    }
  }
}
