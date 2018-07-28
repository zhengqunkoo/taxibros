var pacInputCount = 0, datetimepickerCount = 0;
var lastDatetimepickerId = null;

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
  var datetimepickerId = 'datetimepicker' + datetimepickerCount;
  input.setAttribute('type', 'text');
  input.setAttribute('class', 'form-control td-height');
  input.setAttribute('id', datetimepickerId);
  input.setAttribute('placeholder', 'Pick a date');
  cell.appendChild(input);
  if (innerText !== undefined) {
    $('#' + datetimepickerId).datetimepicker({
      format: 'YYYY/MM/DD HH:mm:ss',
      date: innerText
    }).on('dp.hide', function(e) {
      input.innerText = moment(e.date).format('YYYY/MM/DD HH:mm:ss');
      updateTable();
      lastDatetimepickerId = datetimepickerId;
    });
    input.innerText = innerText;
  } else {
    $('#' + datetimepickerId).datetimepicker({
      format: 'YYYY/MM/DD HH:mm:ss'
    }).on('dp.hide', function(e) {
      input.innerText = moment(e.date).format('YYYY/MM/DD HH:mm:ss');
      updateTable();
      lastDatetimepickerId = datetimepickerId;
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

function addRow(pickupLocationInnerText, pickupTimeInnerText, arrivalLocationInnerText, arrivalTimeInnerText, walkpathGeomInnerText, walkpathInstructionsInnerText, pickupPosInnerText, pickupTaxiCoordsInnerText, radiusInnerText, minutesInnerText, numberInnerText, bestRoadInnerText, bestRoadCoordsInnerText, pathTimeInnerText, pathDistInnerText, totalDistInnerText, journeyGeomInnerText) {
  var row = itineraryTable.getElementsByTagName('tbody')[0].insertRow(-1);
  var pickupLocationCell = row.insertCell(0);
  var pickupTimeCell = row.insertCell(1);
  var arrivalLocationCell = row.insertCell(2);
  var arrivalTimeCell = row.insertCell(3);
  var deleteRowButtonCell = row.insertCell(4);
  var visualizePickupButtonCell = row.insertCell(5);
  var walkpathGeomCell = row.insertCell(6);
  var walkpathInstructionsCell = row.insertCell(7);
  var pickupPosCell = row.insertCell(8);
  var pickupTaxiCoordsCell = row.insertCell(9);
  var radiusCell = row.insertCell(10);
  var minutesCell = row.insertCell(11);
  var numberCell = row.insertCell(12);
  var bestRoadCell = row.insertCell(13);
  var bestRoadCoordsCell = row.insertCell(14);
  var pathTimeCell = row.insertCell(15);
  var pathDistCell = row.insertCell(16);
  var totalDistCell = row.insertCell(17);
  var journeyGeomCell = row.insertCell(18);

  walkpathGeomCell.appendChild(createHiddenText(walkpathGeomInnerText));
  walkpathInstructionsCell.appendChild(createHiddenText(walkpathInstructionsInnerText));
  pickupPosCell.appendChild(createHiddenText(pickupPosInnerText));
  pickupTaxiCoordsCell.appendChild(createHiddenText(pickupTaxiCoordsInnerText));
  radiusCell.appendChild(createHiddenText(radiusInnerText));
  minutesCell.appendChild(createHiddenText(minutesInnerText));
  numberCell.appendChild(createHiddenText(numberInnerText));
  bestRoadCell.appendChild(createHiddenText(bestRoadInnerText));
  bestRoadCoordsCell.appendChild(createHiddenText(bestRoadCoordsInnerText));
  pathTimeCell.appendChild(createHiddenText(pathTimeInnerText));
  pathDistCell.appendChild(createHiddenText(pathDistInnerText));
  totalDistCell.appendChild(createHiddenText(totalDistInnerText));
  journeyGeomCell.appendChild(createHiddenText(journeyGeomInnerText));

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
    ignoreCols: [4, 5],
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
  var walkpathGeom = tr.children('td:nth-child(7)').find('.hide')[0].innerHTML;
  var walkpathInstructions = tr.children('td:nth-child(8)').find('.hide')[0].innerHTML;
  var pickupPos = tr.children('td:nth-child(9)').find('.hide')[0].innerHTML;
  var pickupTaxiCoords = tr.children('td:nth-child(10)').find('.hide')[0].innerHTML;
  var locationRadius = tr.children('td:nth-child(11)').find('.hide')[0].innerHTML;
  var locationMinutes = tr.children('td:nth-child(12)').find('.hide')[0].innerHTML;
  var number = tr.children('td:nth-child(13)').find('.hide')[0].innerHTML;
  var bestRoad = tr.children('td:nth-child(14)').find('.hide')[0].innerHTML;
  var bestRoadCoords = tr.children('td:nth-child(15)').find('.hide')[0].innerHTML;
  var pathTime = tr.children('td:nth-child(16)').find('.hide')[0].innerHTML;
  var pathDist = tr.children('td:nth-child(17)').find('.hide')[0].innerHTML;
  var totalDist = tr.children('td:nth-child(18)').find('.hide')[0].innerHTML;
  var journeyGeom = tr.children('td:nth-child(19)').find('.hide')[0].innerHTML;

  var parsedLatLng = parseLatLng(pickupPos);
  locationCenter = new google.maps.LatLng(parsedLatLng[0], parsedLatLng[1]);
  locationRadius = parseInt(locationRadius);
  locationMinutes = parseInt(locationMinutes);
  pickupTaxiCoords = pickupTaxiCoords.split(';');
  pickupTaxiCoords = pickupTaxiCoords.map(parseLatLng);
  number = parseInt(number);
  var parsedLatLng = parseLatLng(bestRoadCoords);
  bestRoadCoords = new google.maps.LatLng(parsedLatLng[0], parsedLatLng[1]);
  totalDist = parseFloat(totalDist);
  genLoc(locationCenter, locationRadius, locationMinutes, pickupId, walkpathGeom, walkpathInstructions, pickupTaxiCoords, number, bestRoad, bestRoadCoords, pathTime, pathDist, totalDist, journeyGeom);
}

function parseLatLng(latlng) {
  latlng = latlng.split(',');
  return [parseFloat(latlng[0]), parseFloat(latlng[1])];
}

$(function() {
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
