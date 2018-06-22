var pacInputCount = 0, datetimepickerCount = 0;

function createPacInput(cell, isCallGenLoc, innerText) {
  var input = document.createElement('input');
  input.setAttribute('id', 'pac-input' + pacInputCount);
  input.setAttribute('class', 'controls td-height');
  input.setAttribute('type', 'text');
  input.setAttribute('placeholder', 'Search Google Maps');
  cell.appendChild(input);
  if (innerText !== undefined) {
    input.value = innerText;
    input.innerText = innerText;
  }
  initAutocomplete(input, isCallGenLoc);
  pacInputCount++;
}

function createDatetimepicker(cell, innerText) {
  var input = document.createElement('input');
  input.setAttribute('type', 'text');
  input.setAttribute('class', 'form-control td-height');
  input.setAttribute('id', 'datetimepicker' + datetimepickerCount);
  input.setAttribute('placeholder', 'Pick a date');
  cell.appendChild(input);
  if (innerText !== undefined) {
    $('#datetimepicker' + datetimepickerCount).datetimepicker({
      format: 'YYYY/MM/DD HH:mm:ss',
      date: innerText
    }).on('dp.hide', function(e) {
      input.innerText = moment(e.date).format('YYYY/MM/DD HH:mm:ss');
      updateTable();
    });
    input.innerText = innerText;
  } else {
    $('#datetimepicker' + datetimepickerCount).datetimepicker({
      format: 'YYYY/MM/DD HH:mm:ss'
    }).on('dp.hide', function(e) {
      input.innerText = moment(e.date).format('YYYY/MM/DD HH:mm:ss');
      updateTable();
    });
  }
  datetimepickerCount++;
}

function createHiddenText(innerText) {
  var span = document.createElement('span');
  span.setAttribute('class', 'hide');
  if (innerText !== undefined) {
    span.innerText = innerText;
  }
  return span;
}

function createButton(cell, classattr, value) {
  var input = document.createElement('input');
  input.setAttribute('type', 'button');
  input.setAttribute('class', classattr + ' td-height');
  input.setAttribute('value', value);
  cell.appendChild(input);
}

function addRow(pickupLocationInnerText, pickupTimeInnerText, arrivalLocationInnerText, arrivalTimeInnerText, walkpathGeomInnerText, walkpathInstructionsInnerText, pickupPosInnerText, radiusInnerText, minutesInnerText, pickupTaxiCoordsInnerText) {
  var row = itineraryTable.getElementsByTagName('tbody')[0].insertRow(-1);
  var pickupLocationCell = row.insertCell(0);
  var pickupTimeCell = row.insertCell(1);
  var arrivalLocationCell = row.insertCell(2);
  var arrivalTimeCell = row.insertCell(3);
  var deleteRowButtonCell = row.insertCell(4);
  var walkpathGeomCell = row.insertCell(5);
  var walkpathInstructionsCell = row.insertCell(6);
  var pickupPosCell = row.insertCell(7);
  var pickupTaxiCoordsCell = row.insertCell(8);
  var radiusCell = row.insertCell(9);
  var minutesCell = row.insertCell(10);
  var visualizePickupButtonCell = row.insertCell(11);

  walkpathGeomCell.appendChild(createHiddenText(walkpathGeomInnerText));
  walkpathInstructionsCell.appendChild(createHiddenText(walkpathInstructionsInnerText));
  pickupPosCell.appendChild(createHiddenText(pickupPosInnerText));
  pickupTaxiCoordsCell.appendChild(createHiddenText(pickupTaxiCoordsInnerText));
  radiusCell.appendChild(createHiddenText(radiusInnerText));
  minutesCell.appendChild(createHiddenText(minutesInnerText));

  createButton(deleteRowButtonCell, 'deleteRow', 'Delete row');
  createButton(visualizePickupButtonCell, 'visualizePickup', 'Visualize pickup');

  createPacInput(pickupLocationCell, true, pickupLocationInnerText);
  createDatetimepicker(pickupTimeCell, pickupTimeInnerText);
  createPacInput(arrivalLocationCell, false, arrivalLocationInnerText);
  createDatetimepicker(arrivalTimeCell, arrivalTimeInnerText);
  updateTable();
}

function deleteRow() {
  var tr = $(this).closest('tr');
  unsetPickup(tr.children('td:first').find('input').attr('id'));
  tr.remove();
  updateTable();
}

function updateTable() {
  $('#itineraryTable').trigger('update')
  $('#itineraryTable').tableExport().update({
    headings: true,
    footers: true,
    formats: ['csv'],
    filename: 'taxibros',
    bootstrap: true,
    position: "bottom",
    ignoreCols: 4,
    trimWhitespace: false
  });
}

function importFromCsvChange(e) {
  Papa.parse(e.target.files[0], {
    error: function(err, file, inputElem, reason) {
      alert('Papaparse ' + err + reason);
    },
    complete: function(e) {
      importToItineraryTable(e.data);
    }
  });
}

function importToItineraryTable(data) {
  // Clear tbody.
  $("#itineraryTable > tbody").empty();
  // Skip th.
  data.slice(1).forEach(row =>
    addRow.apply(null, row)
  );
  updateTable();
}

// TODO detect offline and use info in imported csv to visualize
// if online, query server database for latest info.
function visualizePickup() {
  var tr = $(this).closest('tr');
  var pickupId = tr.children('td:first').find('input').attr('id');
  var walkpathGeom = tr.children('td:nth-child(6)').find('.hide')[0].innerHTML;
  var walkpathInstructions = tr.children('td:nth-child(7)').find('.hide')[0].innerHTML;
  var pickupPos = tr.children('td:nth-child(8)').find('.hide')[0].innerHTML;
  var pickupTaxiCoords = tr.children('td:nth-child(9)').find('.hide')[0].innerHTML;
  var locationRadius = tr.children('td:nth-child(10)').find('.hide')[0].innerHTML;
  var locationMinutes = tr.children('td:nth-child(11)').find('.hide')[0].innerHTML;

  var parsedLatLng = parseLatLng(pickupPos);
  curLocation = new google.maps.LatLng(parsedLatLng[0], parsedLatLng[1]);
  locationRadius = parseInt(locationRadius);
  locationMinutes = parseInt(locationMinutes);
  pickupTaxiCoords = pickupTaxiCoords.split(';');
  pickupTaxiCoords = pickupTaxiCoords.map(parseLatLng);
  genLoc(curLocation, locationRadius, locationMinutes, pickupId, walkpathGeom, walkpathInstructions, pickupTaxiCoords);
}

function parseLatLng(latlng) {
  latlng = latlng.split(',');
  return [parseFloat(latlng[0]), parseFloat(latlng[1])];
}

$(document).ready(function() {
  $('#addRow').on('click', function() {
    addRow();
  });
  $('#itineraryTable').on('click', '.deleteRow', deleteRow);
  $('#itineraryTable').on('click', '.visualizePickup', visualizePickup);
  $('#importFromCsv').on('change', importFromCsvChange);
  TableExport.prototype.formatConfig.csv.buttonContent = 'Export';

  $('#itineraryTable').tablesorter({
    widthFixed: true,
    widgets: [
      'zebra',
    ],
  }).tablesorterPager({
      container: $("#pager"),
  });

  addRow();
});

