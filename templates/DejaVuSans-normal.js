// DejaVuSans-normal.js
(function (jsPDFAPI) {
    'use strict';
    jsPDFAPI.addFileToVFS('DejaVuSans-normal.ttf', 'AAEAAAALAIAAAwAwT1MvMg8S...');
    jsPDFAPI.addFont('DejaVuSans-normal.ttf', 'DejaVuSans', 'normal');
  })(jsPDF.API);

  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  doc.setFont('DejaVuSans');