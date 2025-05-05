import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from agentpress.tool import ToolResult, openapi_schema, xml_schema
from sandbox.sandbox import SandboxToolsBase
from agentpress.thread_manager import ThreadManager
from utils.logger import logger

class PDFReportTool(SandboxToolsBase):
    """Tool to generate PDF reports from markdown or plain text."""
    def __init__(self, project_id: str, thread_manager: ThreadManager):
        super().__init__(project_id, thread_manager)

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "generate_pdf",
            "description": "Generate a PDF report from markdown or plain text content and save it in the sandbox",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name of the PDF file, e.g., 'report.pdf'"},
                    "content": {"type": "string", "description": "Report content in markdown or plain text"}
                },
                "required": ["filename", "content"]
            }
        }
    })
    @xml_schema(
        tag_name="generate-pdf",
        mappings=[
            {"param_name": "filename", "node_type": "attribute", "path": "."},
            {"param_name": "content", "node_type": "content", "path": "."}
        ],
        example="""
<generate-pdf filename="report.pdf">
# Report Title

Content goes here.
</generate-pdf>
""",
    )
    async def generate_pdf(self, filename: str, content: str) -> ToolResult:
        try:
            # Ensure sandbox is ready
            await self._ensure_sandbox()
            logger.info(f"Generating PDF report: {filename}")
            
            # Build PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=72)
            
            # Create styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=16,
                alignment=TA_CENTER,
                spaceAfter=20
            )
            heading_style = ParagraphStyle(
                'Heading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=10,
                spaceBefore=15
            )
            normal_style = ParagraphStyle(
                'BodyText',
                parent=styles['Normal'],
                fontSize=10,
                spaceBefore=6
            )
            
            # Process content - try to parse as JSON if it looks like JSON
            flowables = []
            try:
                if content.strip().startswith('{') and content.strip().endswith('}'):
                    # Try to parse as JSON
                    json_data = json.loads(content)
                    
                    # Handle title
                    if 'title' in json_data:
                        flowables.append(Paragraph(json_data['title'], title_style))
                        flowables.append(Spacer(1, 20))
                    
                    # Handle companies list
                    if 'companies' in json_data:
                        flowables.append(Paragraph("Company Overview", heading_style))
                        
                        # Create table data
                        table_data = [["Company", "Market Cap", "Revenue", "Employees"]]
                        for company in json_data['companies']:
                            table_data.append([
                                company.get('name', 'N/A'),
                                company.get('market_cap', 'N/A'),
                                company.get('revenue', 'N/A'),
                                str(company.get('employees', 'N/A'))
                            ])
                        
                        # Create table
                        table = Table(table_data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1*inch])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        
                        flowables.append(table)
                        flowables.append(Spacer(1, 20))
                else:
                    # Handle as markdown
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line:
                            flowables.append(Spacer(1, 10))
                            continue
                            
                        if line.startswith('# '):
                            # Title
                            flowables.append(Paragraph(line[2:], title_style))
                        elif line.startswith('## '):
                            # Heading
                            flowables.append(Paragraph(line[3:], heading_style))
                        elif line.startswith('### '):
                            # Subheading
                            flowables.append(Paragraph(line[4:], styles['Heading3']))
                        elif line.startswith('- '):
                            # Bullet point
                            flowables.append(Paragraph(f"• {line[2:]}", normal_style))
                        else:
                            # Normal text
                            flowables.append(Paragraph(line, normal_style))
            except json.JSONDecodeError:
                # If JSON parsing fails, treat as plain text
                logger.warning("Failed to parse content as JSON, treating as plain text")
                lines = content.split('\n')
                for line in lines:
                    if line.strip():
                        flowables.append(Paragraph(line, normal_style))
                        flowables.append(Spacer(1, 6))
            
            # Build the PDF
            doc.build(flowables)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            # Save PDF in sandbox under /workspace/reports
            reports_dir = f"{self.workspace_path}/reports"
            try:
                self.sandbox.fs.create_folder(reports_dir, "755")
            except Exception:
                pass
            
            path = f"{reports_dir}/{filename}"
            self.sandbox.fs.upload_file(path, pdf_bytes)
            logger.info(f"PDF report generated successfully at: {path}")
            
            return self.success_response(f"PDF report generated successfully at: {path}")
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return self.fail_response(f"Error generating PDF: {str(e)}")
