from flask import Flask, render_template, request, send_file
import datetime, json, os
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

DATA_FILE = "data.json"


def safe_int(v):
    try:
        return int(v)
    except:
        return 0


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def next_number(data):
    if len(data) == 0:
        return 1
    return data[-1]["number"] + 1


@app.route("/", methods=["GET", "POST"])
def home():
    data = load_data()
    bill = None

    if request.method == "POST":

        party = request.form.get("party")

        date = request.form.get("date")
        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")

        number = next_number(data)

        items = [
            ("Pants", safe_int(request.form.get("pants_qty")), safe_int(request.form.get("pants_rate"))),
            ("Pants Large", safe_int(request.form.get("pants_l_qty")), safe_int(request.form.get("pants_l_rate"))),
            ("Shirts", safe_int(request.form.get("shirts_qty")), safe_int(request.form.get("shirts_rate"))),
            ("Shirts SML", safe_int(request.form.get("shirts_sml_qty")), safe_int(request.form.get("shirts_sml_rate")))
        ]

        # other item
        other_name = request.form.get("other_name")
        other_qty = safe_int(request.form.get("other_qty"))
        other_rate = safe_int(request.form.get("other_rate"))

        if other_name and other_qty > 0:
            items.append((other_name, other_qty, other_rate))

        total = 0
        final_items = []

        for name, qty, rate in items:
            amount = qty * rate
            total += amount
            final_items.append((name, qty, rate, amount))

        bill = {
            "number": number,
            "party": party,
            "date": date,
            "items": final_items,
            "total": total
        }

        data.append(bill)
        save_data(data)

    return render_template("index.html", bill=bill, history=data)


@app.route("/bill/<int:n>")
def view_bill(n):
    data = load_data()
    for b in data:
        if b["number"] == n:
            return render_template("view.html", bill=b)
    return "Bill not found"


# 🔥 FINAL PROFESSIONAL PDF
@app.route("/pdf/<int:n>")
def generate_pdf(n):
    data = load_data()

    for b in data:
        if b["number"] == n:

            file_name = f"bill_{n}.pdf"
            doc = SimpleDocTemplate(file_name, pagesize=A4)

            styles = getSampleStyleSheet()
            elements = []

            # HEADER
            elements.append(Paragraph("<font size=18><b>SS UNIFORMS</b></font>", styles["Normal"]))
            elements.append(Spacer(1, 10))

            elements.append(Paragraph(f"<b>Bill No:</b> {b['number']}", styles["Normal"]))
            elements.append(Paragraph(f"<b>Party:</b> {b['party']}", styles["Normal"]))
            elements.append(Paragraph(f"<b>Date:</b> {b['date']}", styles["Normal"]))

            elements.append(Spacer(1, 20))

            # TABLE
            table_data = [["Item", "Qty", "Rate", "Amount"]]

            for i in b["items"]:
                table_data.append([i[0], str(i[1]), str(i[2]), str(i[3])])

            table_data.append(["", "", "TOTAL", str(b["total"])])

            table = Table(table_data, colWidths=[180, 60, 80, 100])

            table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563eb")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),

                ("GRID", (0,0), (-1,-1), 0.5, colors.grey),

                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

                ("ALIGN", (1,1), (-1,-1), "CENTER"),

                ("BACKGROUND", (0,1), (-1,-2), colors.whitesmoke),

                ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#d1d5db")),
                ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
            ]))

            elements.append(table)

            elements.append(Spacer(1, 30))
            elements.append(Paragraph("<i>Thank you for your business</i>", styles["Normal"]))

            doc.build(elements)

            return send_file(file_name, as_attachment=True)

    return "Bill not found"


if __name__ == "__main__":
    app.run(debug=True)