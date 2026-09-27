# Codex Task 06: CSV Import Modal HTML & CSS (Metricool UI Style)

## Objective
Implement the UI markup and CSS styling for the CSV Import Modal, matching the Metricool screenshot provided by the user.

## Target Files
1. `social-hub/app/static/index.html`:
   - Add "📄 Import CSV" trigger button in header actions or Evergreen & Bulk tab.
   - Add modal container `#csv-import-modal`:
     - Header: "Import posts from CSV file" + close button (`#btn-close-csv-modal`).
     - Step 1 (Upload State - `#csv-upload-step`): Drag-and-drop file upload zone + file input (`#csv-file-input`) + template download links.
     - Step 2 (Verification Preview State - `#csv-preview-step`):
       - Top toolbar with Date format dropdown (`#csv-date-format`) and Time format dropdown (`#csv-time-format`).
       - Alert boxes on right:
         - Red alert (`#csv-alert-errors`): "Some posts have errors. They will be imported as draft. If the post date is invalid, it will be scheduled today at current time."
         - Red info alert (`#csv-alert-brand-errors`): "Posts with wrong brand names will not be imported."
         - Yellow alert (`#csv-alert-url-warnings`): "Some URLs could not be identified and their preview will not be available, but will be published if the image or video meets the social network's requirements."
       - Post preview list container (`#csv-posts-list`):
         - Post item with error/ok icon, formatted date/time, caption snippet with "More" expander, platform icons, media indicator, and error badges.
     - Footer:
       - `Back` button (`#btn-csv-back`).
       - `Import X posts` button (`#btn-csv-execute-import`).
2. `social-hub/app/static/style.css`:
   - Add CSS styling for:
     - `.csv-import-modal`, `.csv-upload-dropzone`.
     - `.csv-toolbar`, `.csv-format-selects`.
     - `.csv-alert-box` (red, yellow, info styles with icons).
     - `.csv-post-row`, `.csv-post-status-icon`, `.csv-post-meta`, `.csv-post-caption`, `.csv-post-platforms`, `.csv-post-media-tag`, `.csv-post-error-tag`.
     - Responsive adjustments for mobile/desktop.

## Verification
Open `http://localhost:8000`, open the modal, and verify visual alignment with the screenshot.

## Status: Completed ✅
