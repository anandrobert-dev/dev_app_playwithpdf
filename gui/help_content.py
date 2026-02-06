# Help Content for Oi360 Document Suite
# Each tool has its own SOP documentation in HTML format

HELP_CONTENT = {
    "pdf_splitter": """
    <h2>📄 PDF Splitter - User Manual</h2>
    
    <h3>Overview</h3>
    <p>Extract specific pages from a PDF document and save them as a new file.</p>
    
    <h3>Step-by-Step Instructions</h3>
    <ol>
        <li><b>Load Your PDF</b>
            <ul>
                <li>Click <span style="color: #8b5cf6; font-weight: bold;">BROWSE PDF</span> to select a file</li>
                <li>Or drag and drop a PDF directly onto the window</li>
            </ul>
        </li>
        <li><b>View the Preview</b>
            <ul>
                <li>The document preview will appear on the right</li>
                <li>Use <b>Zoom In (+)</b> / <b>Zoom Out (−)</b> to adjust the view</li>
            </ul>
        </li>
        <li><b>Set Page Range</b>
            <ul>
                <li>Enter the <b>Start Page</b> number</li>
                <li>Enter the <b>End Page</b> number</li>
                <li>Example: Start=1, End=5 extracts pages 1 through 5</li>
            </ul>
        </li>
        <li><b>Name Your Output</b>
            <ul>
                <li>Enter a name in the <b>Output File Name</b> field</li>
                <li>The file will be saved to your Downloads folder</li>
            </ul>
        </li>
        <li><b>Split the PDF</b>
            <ul>
                <li>Click <span style="color: #10b981; font-weight: bold;">SPLIT PDF</span></li>
                <li>A success message will confirm the operation</li>
            </ul>
        </li>
    </ol>
    
    <h3>Tips</h3>
    <ul>
        <li>To extract a single page, set Start and End to the same number</li>
        <li>The original PDF remains unchanged</li>
    </ul>
    """,
    
    "pdf_merger": """
    <h2>📑 PDF Merger - User Manual</h2>
    
    <h3>Overview</h3>
    <p>Combine multiple PDF files into a single document. You can select, reorder, and rotate individual pages.</p>
    
    <h3>Step-by-Step Instructions</h3>
    <ol>
        <li><b>Add PDF Files</b>
            <ul>
                <li>Click <span style="color: #8b5cf6; font-weight: bold;">+ ADD DOCUMENTS</span></li>
                <li>Or drag and drop multiple PDFs onto the window</li>
            </ul>
        </li>
        <li><b>Review Page Thumbnails</b>
            <ul>
                <li>All pages appear as visual thumbnails in a grid</li>
                <li>Each page shows its source file and page number</li>
            </ul>
        </li>
        <li><b>Select Pages to Include</b>
            <ul>
                <li>✅ Check the pages you want to keep</li>
                <li>❌ Uncheck pages you want to exclude</li>
                <li>Use <b>SELECT ALL</b> / <b>DESELECT ALL</b> for quick selection</li>
            </ul>
        </li>
        <li><b>Rotate Pages (Optional)</b>
            <ul>
                <li>Click the <b>↻</b> button on any page to rotate it 90°</li>
            </ul>
        </li>
        <li><b>Adjust Zoom (Optional)</b>
            <ul>
                <li>Use <b>+ / −</b> buttons to zoom thumbnails</li>
                <li>Click <b>RESET</b> to return to 100%</li>
            </ul>
        </li>
        <li><b>Generate the Merged PDF</b>
            <ul>
                <li>Click <span style="color: #10b981; font-weight: bold;">>>> GENERATE FINAL PDF <<<</span></li>
                <li>Choose a save location and filename</li>
            </ul>
        </li>
    </ol>
    
    <h3>Tips</h3>
    <ul>
        <li>Pages are merged in the order they appear in the grid</li>
        <li>You can add PDFs from different folders in one session</li>
    </ul>
    """,
    
    "pdf_to_office": """
    <h2>📊 PDF to Office - User Manual</h2>
    
    <h3>Overview</h3>
    <p>Convert PDF documents to Word (.docx), Excel (.xlsx), or plain text (.txt) format.</p>
    
    <h3>Step-by-Step Instructions</h3>
    <ol>
        <li><b>Load Your PDF</b>
            <ul>
                <li>Click <span style="color: #8b5cf6; font-weight: bold;">BROWSE PDF</span></li>
                <li>Or drag and drop a PDF onto the window</li>
            </ul>
        </li>
        <li><b>Select Output Format</b>
            <ul>
                <li><b>Word (.docx)</b> - Best for text documents with formatting</li>
                <li><b>Excel (.xlsx)</b> - Best for tables and data</li>
                <li><b>Text (.txt)</b> - Plain text extraction</li>
            </ul>
        </li>
        <li><b>Preview & Select Pages (Optional)</b>
            <ul>
                <li>Click <span style="color: #06b6d4; font-weight: bold;">👁 PREVIEW & SELECT PAGES</span></li>
                <li>Check/uncheck pages to include</li>
                <li>Use <b>✂️ SELECT REGION</b> to convert only a specific area</li>
            </ul>
        </li>
        <li><b>Convert the Document</b>
            <ul>
                <li>Click <span style="color: #10b981; font-weight: bold;">🔄 CONVERT</span></li>
                <li>The file will be saved to your Downloads folder</li>
            </ul>
        </li>
    </ol>
    
    <h3>Tips</h3>
    <ul>
        <li>For tables (like SOA), use <b>Excel format</b> with <b>Region Selection</b></li>
        <li>Accuracy percentage shows how well the conversion matched the original</li>
    </ul>
    """,
    
    "tiff_splitter": """
    <h2>🖼️ TIFF Splitter - User Manual</h2>
    
    <h3>Overview</h3>
    <p>Split multi-page TIFF images into individual files or page ranges.</p>
    
    <h3>Step-by-Step Instructions</h3>
    <ol>
        <li><b>Load Your TIFF File</b>
            <ul>
                <li>Click <span style="color: #06b6d4; font-weight: bold;">BROWSE TIFF</span></li>
                <li>Or drag and drop a TIFF file onto the window</li>
            </ul>
        </li>
        <li><b>View the Preview</b>
            <ul>
                <li>Navigate between pages using the page controls</li>
                <li>Use zoom controls to adjust the view</li>
            </ul>
        </li>
        <li><b>Set Page Range</b>
            <ul>
                <li>Enter the <b>Start Page</b> and <b>End Page</b></li>
                <li>Leave as default to extract all pages</li>
            </ul>
        </li>
        <li><b>Name Your Output</b>
            <ul>
                <li>Enter a name in the <b>Output File Name</b> field</li>
            </ul>
        </li>
        <li><b>Split the TIFF</b>
            <ul>
                <li>Click <span style="color: #10b981; font-weight: bold;">SPLIT TIFF</span></li>
            </ul>
        </li>
    </ol>
    
    <h3>Tips</h3>
    <ul>
        <li>Output files are saved in your Downloads folder</li>
        <li>Multi-page TIFFs are common in scanned documents</li>
    </ul>
    """,
    
    "image_to_pdf": """
    <h2>📷 Image → PDF - User Manual</h2>
    
    <h3>Overview</h3>
    <p>Convert multiple images (JPG, PNG, TIFF, etc.) into a single PDF document.</p>
    
    <h3>Step-by-Step Instructions</h3>
    <ol>
        <li><b>Add Images</b>
            <ul>
                <li>Click <span style="color: #ec4899; font-weight: bold;">+ ADD IMAGES</span></li>
                <li>Or drag and drop images onto the window</li>
                <li>Supported formats: JPG, JPEG, PNG, TIFF, BMP, GIF</li>
            </ul>
        </li>
        <li><b>Review Thumbnails</b>
            <ul>
                <li>All images appear as thumbnails in the grid</li>
                <li>Each image becomes one page in the PDF</li>
            </ul>
        </li>
        <li><b>Reorder Images (Optional)</b>
            <ul>
                <li>Drag and drop thumbnails to change the order</li>
            </ul>
        </li>
        <li><b>Select Images to Include</b>
            <ul>
                <li>Check/uncheck images using the checkbox on each thumbnail</li>
            </ul>
        </li>
        <li><b>Generate the PDF</b>
            <ul>
                <li>Click <span style="color: #10b981; font-weight: bold;">>>> GENERATE PDF <<<</span></li>
                <li>Choose a save location and filename</li>
            </ul>
        </li>
    </ol>
    
    <h3>Tips</h3>
    <ul>
        <li>Images are automatically scaled to fit the PDF page</li>
        <li>The order of thumbnails = order of pages in PDF</li>
    </ul>
    """,
    
    "ocr_engine": """
    <h2>🔍 OCR Engine - User Manual</h2>
    
    <h3>Overview</h3>
    <p>Extract text from images and scanned PDFs using Optical Character Recognition (OCR). Includes translation support.</p>
    
    <h3>Step-by-Step Instructions</h3>
    <ol>
        <li><b>Load Your Document</b>
            <ul>
                <li>Click <span style="color: #FF6B00; font-weight: bold;">BROWSE FILE</span></li>
                <li>Supported: Images (JPG, PNG, TIFF) and PDFs</li>
            </ul>
        </li>
        <li><b>View the Preview</b>
            <ul>
                <li>The document appears in the preview panel</li>
                <li>Use zoom controls to adjust the view</li>
            </ul>
        </li>
        <li><b>Select Region (Optional)</b>
            <ul>
                <li>Click <b>✂️ SELECT</b> to enable region mode</li>
                <li>Draw a rectangle around the text area</li>
                <li>Only the selected area will be processed</li>
            </ul>
        </li>
        <li><b>Choose OCR Language</b>
            <ul>
                <li>Select the language of the text in your document</li>
                <li>Supported: English, Hindi, French, German, Spanish, and more</li>
            </ul>
        </li>
        <li><b>Extract Text</b>
            <ul>
                <li>Click <span style="color: #10b981; font-weight: bold;">EXTRACT TEXT</span></li>
                <li>The recognized text appears in the text area</li>
            </ul>
        </li>
        <li><b>Translate (Optional)</b>
            <ul>
                <li>Select the target language from <b>Translate To</b></li>
                <li>Click <b>🌐 TRANSLATE TEXT</b></li>
            </ul>
        </li>
        <li><b>Save the Text</b>
            <ul>
                <li>Click <b>💾 SAVE TEXT</b> to save as a .txt file</li>
            </ul>
        </li>
    </ol>
    
    <h3>Tips</h3>
    <ul>
        <li>Higher quality images = better OCR accuracy</li>
        <li>For Hindi text, select "Hindi" as the OCR language</li>
        <li>Translation works offline for Hindi ↔ English</li>
    </ul>
    """
}
