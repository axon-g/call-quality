import sys

sink = sys.stdout

sink = open("/home/kinoko/GIT/axon/call-quality/src/exp04/build/demo.html", "w")

bitrate = 48
frame_size = 60

frame_sizes = [10, 20, 40, 60]
bitrates = [64, 48, 32]

exp_losses = [90, 80, 70, 60, 50, 40, 30, 20, 10]
drop_rates = [10, 20, 30, 40, 50]


def write_start(sink):
    sink.write(
    """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Opus samples</title>
                <style>
            :root{
                --bg: #0f1724;            /* dark page background */
                --card: #0b1220;          /* card background */
                --muted: #9fb6d8;         /* muted text */
                --accent: linear-gradient(135deg,#4f9eed,#2b64d8);
                --blue-600: #2b64d8;
                --blue-500: #4f9eed;
                --glass: rgba(255,255,255,0.03);
                --row-alt: rgba(255,255,255,0.02);
                --shadow: 0 6px 24px rgba(11,18,32,0.7);
                --radius: 12px;
                font-family: Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial;
            }

            html,body{
                height:100%;
                margin:0;
            }

            .wrap{
                margin:48px auto;
                padding:28px;
            }

            .card{
                background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
                border-radius: var(--radius);
                box-shadow: var(--shadow);
                overflow:hidden;
                border: 1px solid rgba(255,255,255,0.04);
                margin-top: 3em;
            }

            header.card-header{
                display:flex;
                align-items:center;
                gap:16px;
                padding:20px 24px;
                border-bottom:1px solid rgba(255,255,255,0.03);
                background: linear-gradient(90deg, rgba(43,100,216,0.06), rgba(79,158,237,0.03));
            }
            .logo {
                width:44px;height:44px;border-radius:10px;
                background:var(--accent);
                box-shadow: 0 6px 18px rgba(79,158,237,0.12), inset 0 -6px 18px rgba(255,255,255,0.06);
                display:flex;align-items:center;justify-content:center;font-weight:700;color:white;
                font-size:24px;
            }
            h1 { margin:0; font-size:24px; letter-spacing:0.2px; }
            p.lead { margin:0; color:var(--muted); font-size:13px; }

            .table-wrap{
                overflow:auto;
                width:100%;
            }

            table.stylish {
                width:100%;
                border-collapse:separate;
                border-spacing:0;
                min-width:720px; /* allow horizontal scroll on small screens */
            }

            /* sticky header */
            thead th {
                position: sticky;
                top:0;
                z-index:2;
                background: linear-gradient(180deg, rgba(11,18,32,0.65), rgba(11,18,32,0.5));
                backdrop-filter: blur(4px);
                padding:20px 18px;
                text-align:left;
                font-size:13px;
                color: #dff0ff;
                letter-spacing:0.3px;
                border-bottom: 1px solid rgba(255,255,255,0.04);
            }

            thead th .col-head {
                display:flex; align-items:center; gap:8px;
            }
            thead th .col-title { font-weight:600; }

            /* rows */
            tbody tr {
                transition: background .18s ease, transform .12s ease;
            }
            tbody tr:nth-child(even) { background: var(--row-alt); }
            tbody td {
                padding:14px 18px;
                border-bottom: 1px dashed rgba(255,255,255,0.02);
                font-size:20px;
            }

            tbody tr:hover {
                background: linear-gradient(90deg, rgba(43,100,216,0.06), rgba(79,158,237,0.02));
                transform: translateY(-2px);
            }

            /* badges and numeric cells */
            .badge {
                display:inline-block;
                padding:6px 10px;
                border-radius:999px;
                background: linear-gradient(90deg,var(--blue-500),var(--blue-600));
                color:white;font-weight:600;font-size:13px;
                box-shadow: 0 4px 10px rgba(43,100,216,0.12);
            }

            td.center { text-align:center; }
            td.right { text-align:right; font-variant-numeric: tabular-nums; }

            /* footer / summary row */
            tfoot td { padding:12px 18px; color:var(--muted); font-size:13px; background: linear-gradient(180deg, rgba(255,255,255,0.01), transparent); }

            /* responsive tweaks */
            @media (max-width: 760px){
                header.card-header{ padding:14px; gap:12px; }
                thead th, tbody td { padding:10px 12px; font-size:13px; }
                .wrap{ margin:18px 12px; }
            }
        </style>
    </head>
    <body>
    <div class="wrap">
    \n""")

def write_end(sink):
    sink.write("""</div></body></html>\n\n""")

def write_table(table_ix, sink, frame_size: int, bitrate: int):
    # sink.write(f"<h2>Frame size={frame_size} Bitrate={bitrate}kbps </h2>\n")
    # sink.write("<table>\n")

    sink.write(f"""
    <div class="card" role="region" aria-label="Stylish bluish table">
    <header class="card-header">
        <div class="logo">{table_ix}</div>
        <div>
            <h1> Frame size={frame_size} Bitrate={bitrate}kbps</h1>
            <p class="lead"> Very small framesize </p>
        </div>
    </header>

    <div class="table-wrap">
    <table class="stylish" aria-describedby="desc">
    """)
    sink.write("<tr>\n")
    sink.write("<th> Expected loss </th>\n")
    for drop in drop_rates:
        row = f"<th> drop={drop}% </th>\n"
        sink.write(row)
    sink.write("</tr>\n")


    sink.write("<tr>")
    sink.write(f"<td> μ-law</td>\n")
    for drop in drop_rates:
        fpath_wav = f"./decoded-wav/g_23_sample.ulaw.frame{frame_size}.drop{drop}.wav"
        audio_elem = f"""<audio controls> <source src="{fpath_wav}" type="audio/wav"> Your browser does not support the audio element.</audio>"""
        row = f"<td> {audio_elem} </td>\n"
        sink.write(row)
    sink.write("</tr>\n")

    for loss in exp_losses:
        sink.write("<tr>")
        sink.write(f"<td>{loss}%</td>\n")
        for drop in drop_rates:
            fpath_wav = f"./decoded-wav/g_23_sample.bitrate{bitrate}.frame{frame_size}.eloss{loss}.drop{drop}.wav"
            audio_elem = f"""<audio controls> <source src="{fpath_wav}" type="audio/wav"> Your browser does not support the audio element.</audio>"""
            row = f"<td> {audio_elem} </td>\n"
            sink.write(row)
    sink.write("</tr>\n")
    sink.write("</table></div></div>\n\n\n")




write_start(sink)
n_table = 0

for frame_size in frame_sizes:
    for bitrate in bitrates:
        n_table += 1
        write_table(n_table, sink, frame_size, bitrate)
write_end(sink)


sink.close()

#f"g_23_sample.bitrate48.frame60.eloss{loss}.drop{drop}.wav"