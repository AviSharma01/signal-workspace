"""Small synthetic native-text PDFs for malformed/missing-value acceptance tests.

The eight columns and separate main/detail border segments mirror the measured
House layout. All values are test data; these bytes never enter real storage.
No PDF extraction helper is used to generate the expected cells.
"""


def ptr_pdf(rows: list[list[str]]) -> bytes:
    columns = [22, 60, 99, 244, 310, 363, 428, 503, 575]
    headers = ["ID", "Owner", "Asset", "Transaction\nType", "Date", "Notification\nDate", "Amount", "Cap.\nGains >\n$200?"]
    commands = []

    def rect(x, top, width, height):
        commands.append(f"0.93 g {x} {792-top-height} {width} {height} re f")

    def text(x, top, value):
        for line_index, line in enumerate(value.split("\n")):
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"0 g BT /F1 8 Tf 1 0 0 1 {x} {792-top-line_index*10} Tm ({escaped}) Tj ET")

    text(22, 40, "Periodic Transaction Report - synthetic test fixture")
    for index, header in enumerate(headers):
        rect(columns[index], 60, columns[index+1]-columns[index], 40)
        text(columns[index]+3, 70, header)
    top = 100
    for row in rows:
        for index, value in enumerate(row):
            text(columns[index]+3, top+12, value)
        rect(22, top, 0.75, 35)
        rect(575, top, 0.75, 35)
        top += 35
        text(102, top+12, "Filing Status: New")
        rect(22, top, 0.75, 25)
        rect(575, top, 0.75, 25)
        top += 25
    stream = "\n".join(commands).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream",
    ]
    result = b"%PDF-1.4\n"
    offsets = []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(result)
    result += b"xref\n0 6\n0000000000 65535 f \n"
    result += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    return result + f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
