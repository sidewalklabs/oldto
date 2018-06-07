// This module allows both the photo viewer and corrections UI to share logic.

// See get_source_properties in generate_geojson.py
const ALL_FIELDS = [
  'date',  // Both
  'physical_desc', 'citation', 'condition', 'scope',  // Toronto Archives
  'creator', 'description', 'subject' // TPL
];

export function fillDetailsPanel(photoId, info, $pane) {
  const {archives_fields, geocode, url, tpl_fields} = info;

  $pane.find('a.link').attr('href', url);
  $pane.find('a.link.source')
    .text(tpl_fields ? 'Toronto Public Library' : 'City of Toronto Archives');
  $pane.find('a.feedback-button').attr('href', `/corrections/?id=${photoId}`);

  const fields = archives_fields || tpl_fields;

  for (const k of ALL_FIELDS) {
    const v = fields[k];
    if (v) {
      $pane.find(`.${k}`).show();
      $pane.find(`.value.${k}, a.${k}`).text(v || '');
    } else {
      $pane.find(`.${k}`).hide();  // hide both key & value if value is missing.
    }
  }

  $pane.find('.title').text(info.title);
  $pane.find('.geocode-debug').text(JSON.stringify(geocode, null, 2));
}
