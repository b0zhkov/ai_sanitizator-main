const Export = (() => {
    function downloadTxt(text) {
        if (!text) return;
        _triggerDownload(new Blob([text], { type: 'text/plain' }), 'sanitized_output.txt');
    }

    async function downloadDocx(text) {
        if (!text) return;
        if (!window.docx) {
            console.error("docx library not loaded");
            return;
        }

        const { Document, Packer, Paragraph, TextRun, HeadingLevel } = window.docx;

        const doc = new Document({
            sections: [{
                properties: {},
                children: [
                    new Paragraph({
                        text: "Sanitized Output",
                        heading: HeadingLevel.HEADING_1,
                        spacing: { after: 200 },
                    }),
                    ...text.split('\n').map(line => new Paragraph({
                        children: [new TextRun(line)],
                        spacing: { after: 100 },
                    }))
                ],
            }],
        });

        const blob = await Packer.toBlob(doc);
        _triggerDownload(blob, 'sanitized_output.docx');
    }

    function downloadPdf(text) {
        if (!text) return;
        if (!window.jspdf) {
            console.error("jspdf library not loaded");
            return;
        }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        // Simple text wrapping
        const splitText = doc.splitTextToSize(text, 180); // 180mm width (A4 is approx 210mm)

        doc.setFontSize(16);
        doc.text("Sanitized Output", 15, 15);

        doc.setFontSize(11);
        doc.setFont("helvetica", "normal");

        let y = 25;
        // Check if text exceeds page height
        const pageHeight = doc.internal.pageSize.height;

        splitText.forEach(line => {
            if (y > pageHeight - 15) {
                doc.addPage();
                y = 15;
            }
            doc.text(line, 15, y);
            y += 6; // Line height
        });

        doc.save('sanitized_output.pdf');
    }

    function _triggerDownload(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    return { downloadTxt, downloadDocx, downloadPdf };
})();
