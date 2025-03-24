import os
from bs4 import BeautifulSoup
import weasyprint
from pathlib import Path
import glob

def create_pdfs_from_tables(template_path, tables_folder, output_folder, base_font_size=12):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Load the HTML template
    with open(template_path, 'r', encoding='utf-8') as file:
        template_html = file.read()
    
    # Get all table HTML files
    table_files = glob.glob(os.path.join(tables_folder, '*.html'))
    
    for i, table_file in enumerate(table_files):
        table_filename = os.path.basename(table_file)
        
        # Load the table HTML
        with open(table_file, 'r', encoding='utf-8') as file:
            table_html = file.read()
        
        # Create soup object from template
        soup = BeautifulSoup(template_html, 'html.parser')
        
        # Find the body tag to append the table
        body_tag = soup.find('body')
        
        # Create a new tag for the table and insert it
        table_soup = BeautifulSoup(table_html, 'html.parser')
        body_tag.append(table_soup)
        
        # Add custom style to control font size
        style_tag = soup.new_tag('style')
        style_tag.string = f"""
            table {{
                font-size: {base_font_size}px;
                width: 100%;
                page-break-inside: avoid;
            }}
        """
        soup.head.append(style_tag)
        
        # Generate the new HTML with the table inserted
        final_html = str(soup)
        
        # Temporary HTML file path
        temp_html_path = os.path.join(output_folder, f"temp_{i}.html")
        
        # Write to temporary HTML file
        with open(temp_html_path, 'w', encoding='utf-8') as file:
            file.write(final_html)
        
        # Output PDF path
        pdf_path = os.path.join(output_folder, f"{Path(table_filename).stem}.pdf")
        
        # Try generating PDF with current font size
        current_font_size = base_font_size
        pdf_fits_one_page = False
        
        while not pdf_fits_one_page and current_font_size >= 5:  # Set minimum font size to 8
            # Update font size in the HTML
            soup = BeautifulSoup(final_html, 'html.parser')
            style_tags = soup.find_all('style')
            for style_tag in style_tags:
                if 'font-size' in style_tag.string:
                    style_tag.string = f"""
                        table {{
                            font-size: {current_font_size}px;
                            width: 100%;
                            page-break-inside: avoid;
                        }}
                    """
            
            final_html_adjusted = str(soup)
            
            # Write adjusted HTML
            with open(temp_html_path, 'w', encoding='utf-8') as file:
                file.write(final_html_adjusted)
            
            # Convert to PDF
            pdf = weasyprint.HTML(filename=temp_html_path).render()
            
            # Check if PDF fits on one page
            if len(pdf.pages) <= 1:
                pdf_fits_one_page = True
                pdf.write_pdf(pdf_path)
                print(f"Generated PDF: {pdf_path} with font size {current_font_size}px")
            else:
                # Reduce font size and try again
                current_font_size -= 1
        
        # If we couldn't fit on one page even with minimum font size
        if not pdf_fits_one_page:
            # Use the minimum font size and generate PDF anyway
            soup = BeautifulSoup(final_html, 'html.parser')
            style_tags = soup.find_all('style')
            for style_tag in style_tags:
                if 'font-size' in style_tag.string:
                    style_tag.string = f"""
                        table {{
                            font-size: 5px;
                            width: 100%;
                            page-break-inside: avoid;
                        }}
                    """
            
            final_html_minimum = str(soup)
            
            with open(temp_html_path, 'w', encoding='utf-8') as file:
                file.write(final_html_minimum)
            
            # Generate PDF with minimum font size
            weasyprint.HTML(filename=temp_html_path).write_pdf(pdf_path)
            print(f"Warning: {pdf_path} doesn't fit on one page. Generated with minimum font size 8px.")
        
        # Clean up temporary HTML file
        os.remove(temp_html_path)

# Example usage
currPath = os.getcwd()
template_path = os.path.join(currPath, "template.html")  # Your main HTML template
tables_folder = os.path.join(currPath, "data/groundtruth") # Folder containing your table HTML files
output_folder = os.path.join(currPath, "data/pdfs_sp")  # Folder where PDFs will be saved
base_font_size = 12  # Starting font size to try

create_pdfs_from_tables(template_path, tables_folder, output_folder, base_font_size)
