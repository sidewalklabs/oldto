import {initializeMap, fillPopularImagesPanel} from './viewer';
import './app-history';
import './search';

$(function() {
  fillPopularImagesPanel();
  initializeMap();
});
