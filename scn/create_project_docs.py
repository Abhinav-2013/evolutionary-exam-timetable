from pathlib import Path
import json
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, KeepTogether, Flowable)
from reportlab.pdfgen import canvas
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
DATA = json.loads((ROOT / "output_date_check" / "run_summary.json").read_text(encoding="utf-8"))
PDF = OUT / "exam_timetable_project_report.pdf"
PPTX = OUT / "exam_timetable_project_presentation.pptx"

NAVY = "14213D"
BLUE = "4F6FE8"
TEAL = "20A486"
GOLD = "E7A84B"
RED = "D96370"
INK = "24324A"
MUTED = "64748B"
PALE = "F2F5FA"
WHITE = "FFFFFF"

def hexrgb(value):
    return RGBColor.from_string(value)

def add_text(slide, x, y, w, h, text, size=16, color=INK, bold=False, font="Aptos", align=None):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear(); tf.word_wrap = True
    tf.margin_left = Inches(.02); tf.margin_right = Inches(.02)
    tf.margin_top = Inches(.02); tf.margin_bottom = Inches(.02)
    p = tf.paragraphs[0]
    if align is not None: p.alignment = align
    run = p.add_run(); run.text = text
    run.font.name = font; run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = hexrgb(color)
    return box

def add_bullets(slide, x, y, w, h, items, size=17, color=INK, gap=10):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf=box.text_frame; tf.clear(); tf.word_wrap=True
    tf.margin_left=Inches(.04);tf.margin_right=Inches(.04)
    for i,item in enumerate(items):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.text="•  "+item; p.font.name="Aptos"; p.font.size=Pt(size); p.font.color.rgb=hexrgb(color)
        p.space_after=Pt(gap)
    return box

def base_slide(prs, title, kicker=None):
    slide=prs.slides.add_slide(prs.slide_layouts[6])
    bg=slide.background.fill;bg.solid();bg.fore_color.rgb=hexrgb(PALE)
    if kicker: add_text(slide,.62,.34,11.8,.25,kicker.upper(),10,BLUE,True)
    add_text(slide,.62,.68,12.0,.65,title,27,NAVY,True)
    bar=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(.62), Inches(1.42), Inches(.7), Inches(.055))
    bar.fill.solid();bar.fill.fore_color.rgb=hexrgb(TEAL);bar.line.fill.background()
    add_text(slide,.62,7.12,12,.2,"EXAM TIMETABLE OPTIMIZATION  ·  SYNTHETIC PROJECT PROTOTYPE",8,MUTED)
    return slide

def card(slide,x,y,w,h,title,body,accent=BLUE):
    sh=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid();sh.fill.fore_color.rgb=hexrgb(WHITE);sh.line.color.rgb=hexrgb("DCE3EE")
    add_text(slide,x+.18,y+.15,w-.36,.35,title,15,accent,True)
    add_text(slide,x+.18,y+.56,w-.36,h-.7,body,12,INK)

def add_table(slide, x,y,w,h, headers, rows, widths=None, fs=11):
    shape=slide.shapes.add_table(len(rows)+1,len(headers), Inches(x), Inches(y), Inches(w), Inches(h))
    table=shape.table
    if widths:
        for col,frac in zip(table.columns,widths): col.width=Inches(w*frac)
    allrows=[headers]+rows
    for ri,row in enumerate(allrows):
        for ci,val in enumerate(row):
            cell=table.cell(ri,ci);cell.text=str(val);cell.margin_left=Inches(.08);cell.margin_right=Inches(.06);cell.margin_top=Inches(.04);cell.margin_bottom=Inches(.04)
            cell.fill.solid();cell.fill.fore_color.rgb=hexrgb(NAVY if ri==0 else (WHITE if ri%2 else "F7F9FC"))
            for p in cell.text_frame.paragraphs:
                p.font.name="Aptos";p.font.size=Pt(fs);p.font.bold=ri==0;p.font.color.rgb=hexrgb(WHITE if ri==0 else INK)
    return table

def build_pptx():
    prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
    # Cover
    slide=prs.slides.add_slide(prs.slide_layouts[6]);slide.background.fill.solid();slide.background.fill.fore_color.rgb=hexrgb(NAVY)
    add_text(slide,.85,.72,11,.32,"COMPUTER SCIENCE PROJECT  /  OPTIMIZATION",11,"AFC3FF",True)
    add_text(slide,.85,1.55,10.8,1.4,"Evolutionary Algorithms\nfor Exam Timetabling",36,WHITE,True)
    add_text(slide,.88,3.45,9.4,.8,"A comparison of Genetic Algorithm, Evolution Strategy, and Evolutionary Programming",18,"D4DEF3")
    # decorative schedule blocks
    for i,(lab,col) in enumerate([("GA",BLUE),("ES",TEAL),("EP",GOLD)]):
        x=.9+i*1.65; sh=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(5.25), Inches(1.35), Inches(.72));sh.fill.solid();sh.fill.fore_color.rgb=hexrgb(col);sh.line.fill.background();sh.text=lab
        sh.text_frame.paragraphs[0].font.color.rgb=hexrgb(WHITE);sh.text_frame.paragraphs[0].font.bold=True;sh.text_frame.paragraphs[0].font.size=Pt(18);sh.text_frame.paragraphs[0].alignment=PP_ALIGN.CENTER
    add_text(slide,.9,6.8,11,.25,"Prototype uses fabricated subjects and student records; results are illustrative.",10,"B8C5DB")

    s=base_slide(prs,"The scheduling problem","01 · Problem")
    add_text(s,.75,1.78,5.6,1.2,"Assign every exam paper to a date, session, and set of halls while satisfying hard constraints.",21,INK,True)
    card(s,6.8,1.8,2.7,1.65,"Hard constraints","• No student has two simultaneous exams\n• Required halls fit within available rooms",RED)
    card(s,9.75,1.8,2.8,1.65,"Soft objectives","• Reduce consecutive-session papers\n• Balance enrollment load by session",TEAL)
    add_bullets(s,.82,3.45,11.5,2.8,["Exam windows are chosen with start and end dates; weekends are skipped.","Each weekday offers two sessions: 08:00–09:30 and 12:00–13:30.","A large course can be seated across multiple halls, each modeled at 60 seats."],17)

    s=base_slide(prs,"Synthetic data used in the demo","02 · Inputs")
    rows=[["Core CSE","CS",600],["AI & ML","AM",240],["AI & Data Science","AD",240],["CS & Business Systems","CB",240],["Information Science","IS",240],["CS & IoT","CI",240]]
    add_table(s,.8,1.8,5.3,3.5,["Branch","USN suffix","Students"],rows,[.53,.23,.24],13)
    card(s,6.45,1.82,5.8,1.45,"Exam inventory","73 generated exam entries across Semesters III–VIII. Shared subjects are combined into cross-branch exams.",BLUE)
    card(s,6.45,3.52,5.8,1.45,"Rooms","40 rooms: 201–220 and 401–420. Capacity is modeled as 60 seats per room.",TEAL)
    add_text(s,.85,5.75,11.7,.7,"Important: branch subjects, enrollments, and USNs are fabricated for a prototype. They are not official student or registrar data.",14,RED,True)

    s=base_slide(prs,"How a candidate timetable is represented","03 · Solution design")
    labels=[("01","Courses + enrollment"),("02","Session assignment"),("03","Room allocation"),("04","Fitness evaluation"),("05","Compare + export")]
    for i,(n,t) in enumerate(labels):
        x=.72+i*2.52
        sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(2.3), Inches(2.1), Inches(1.1));sh.fill.solid();sh.fill.fore_color.rgb=hexrgb(WHITE);sh.line.color.rgb=hexrgb("DCE3EE")
        add_text(s,x+.14,2.48,.5,.3,n,14,BLUE,True);add_text(s,x+.14,2.88,1.85,.4,t,13,NAVY,True)
        if i<4:
            ln=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x+2.12), Inches(2.85), Inches(x+2.45), Inches(2.85));ln.line.color.rgb=hexrgb(TEAL);ln.line.width=Pt(2)
    add_bullets(s,.9,4.05,11.3,2.0,["Candidate = one session index per exam paper; the corresponding date and period come from the selected calendar.","A repair step reassigns conflicting papers and moves exams when a session exceeds hall capacity.","The best feasible candidate is written as a timetable CSV with dates, periods, enrollment, halls, and synthetic USNs."],16)

    s=base_slide(prs,"Fitness formula and priorities","04 · Evaluation")
    add_text(s,.9,1.85,11.5,.6,"Penalty = 1,000,000 × student clashes + 1,000,000 × hall overflow + 100 × back-to-back pairs + load imbalance",18,BLUE,True)
    rows=[["Student clashes","Same student assigned two exams in one session","Hard; target 0","1,000,000"],["Hall overflow","Halls needed beyond 40 available in a session","Hard; target 0","1,000,000"],["Back-to-back pairs","One student has exams in consecutive session numbers","Soft; minimize","100"],["Load imbalance","Variance-like deviation of total exam enrollment per session","Soft; minimize","1"]]
    add_table(s,.8,2.65,11.8,2.75,["Metric","Meaning","Priority","Weight"],rows,[.2,.42,.2,.18],11)
    add_text(s,.9,5.7,11.4,.8,"Winner selection in code is lexicographic: feasible first, then fewer back-to-back pairs, then lower load imbalance. This can differ from simply choosing the lowest weighted total score.",13,RED,True)

    s=base_slide(prs,"Three evolutionary search methods","05 · Algorithms")
    card(s,.8,1.85,3.75,2.6,"Genetic Algorithm (GA)","Selects stronger schedules, combines parent assignments with crossover, then mutates some exams. Useful when parts of two good schedules can be recombined.",BLUE)
    card(s,4.8,1.85,3.75,2.6,"Evolution Strategy (ES)","Uses mutation to create offspring and keeps the strongest candidates in a (μ + λ) survivor pool. Often associated with numeric optimization; here it is adapted to discrete session assignments.",TEAL)
    card(s,8.8,1.85,3.75,2.6,"Evolutionary Programming (EP)","Mutates parent schedules and applies pairwise competition among parents and offspring. It emphasizes mutation and selection rather than crossover.",GOLD)
    add_text(s,.92,5.0,11.6,.95,"All three use the same timetable encoding, repair logic, score, population/generation budget, and seed for a fair educational comparison. ES and EP have multiple variants; these are project implementations, not the only canonical forms.",14,INK)

    s=base_slide(prs,"Demonstration comparison","06 · Sample result")
    best=DATA["best_algorithm"]
    add_table(s,.8,1.8,11.7,2.4,["Method","Fitness penalty","Clashes","Hall overflow","Back-to-back","Load penalty","Runtime"],[[r["algorithm"],f'{r["fitness"]:,}',r["hard_conflicts"],r["room_overflow"],f'{r["back_to_back_pairs"]:,}',f'{r["load_imbalance"]:,}',f'{r["runtime_seconds"]:.3f}s'] for r in DATA["comparison"]],[.11,.16,.11,.14,.16,.17,.15],10)
    winner=next(r for r in DATA["comparison"] if r["algorithm"]==best)
    add_text(s,.9,4.55,11.5,.65,f"Best by the project’s feasibility-first ranking: {best} ({winner['back_to_back_pairs']:,} back-to-back pairs).",19,TEAL,True)
    add_text(s,.9,5.35,11.5,1.0,f"Run settings: {DATA['students']:,} synthetic students; {DATA['exams']} exam entries; {DATA['sessions']} sessions over {len(DATA['exam_dates'])} weekdays ({DATA['start_date']} to {DATA['end_date']}); population {DATA['population']}; {DATA['generations']} generations; seed {DATA['seed']}. Demo-quality search budget: results illustrate behavior, not an optimized institutional schedule.",12,MUTED)

    s=base_slide(prs,"Technology stack and modules","07 · Implementation")
    rows=[["Python 3","Optimization and data generation","main.py"],["Python standard library","Randomized search, conflict graph, CSV/JSON, local HTTP server","main.py, app.py"],["HTML + CSS + JavaScript","Neumorphic dashboard, date controls, charts, semester tables","dashboard.html"],["Canvas API","Fitness component and session-load charts","dashboard.html"],["CSV / JSON","Timetable, comparison metrics, and run metadata","output/ files"]]
    add_table(s,.8,1.8,11.7,3.55,["Technology","Role","Module"],rows,[.23,.52,.25],12)
    add_text(s,.9,5.85,11.5,.6,"No external front-end packages are required. The local server defaults to port 8766.",13,TEAL,True)

    s=base_slide(prs,"What the prototype does not model yet","08 · Limits and next steps")
    add_bullets(s,.9,1.9,11.4,3.6,["Replace fabricated courses and student links with verified registrar exports.","Add room availability, exam-specific hall requirements, accessibility needs, holidays, and invigilator constraints.","Represent elective enrollment accurately; the current model assumes each student takes every subject in their branch-semester curriculum.","Benchmark each algorithm over many seeds and report mean/best/worst results; current comparison uses one seed and a small demo budget.","Tune fitness priorities with college staff and validate every generated timetable before publication."],16)
    add_text(s,.9,5.85,11.5,.65,"The prototype demonstrates the workflow. Operational scheduling needs validated inputs and additional constraint checks.",16,RED,True)

    prs.save(PPTX)

class SectionBar(Flowable):
    def __init__(self, title, color=BLUE): super().__init__(); self.title=title; self.color=colors.HexColor('#'+color); self.height=23
    def draw(self):
        self.canv.setFillColor(self.color);self.canv.roundRect(0,2,5*mm,5*mm,2,fill=1,stroke=0)
        self.canv.setFillColor(colors.HexColor('#'+NAVY));self.canv.setFont('Helvetica-Bold',13);self.canv.drawString(9*mm,3,self.title)

def draw_footer(c,doc):
    c.saveState();w,h=A4;c.setStrokeColor(colors.HexColor('#DCE3EE'));c.line(18*mm,15*mm,w-18*mm,15*mm)
    c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#64748B'));c.drawString(18*mm,10*mm,'Exam timetable optimization · synthetic prototype')
    c.drawRightString(w-18*mm,10*mm,f'Page {doc.page}');c.restoreState()

def build_pdf():
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CoverTitle',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=28,leading=34,textColor=colors.HexColor('#'+NAVY),alignment=TA_LEFT,spaceAfter=14))
    styles.add(ParagraphStyle(name='Deck',parent=styles['Normal'],fontSize=13,leading=19,textColor=colors.HexColor('#'+MUTED),spaceAfter=9))
    styles.add(ParagraphStyle(name='BodyX',parent=styles['BodyText'],fontSize=9.5,leading=14,textColor=colors.HexColor('#'+INK),spaceAfter=7))
    styles.add(ParagraphStyle(name='SmallX',parent=styles['BodyText'],fontSize=8,leading=11,textColor=colors.HexColor('#'+MUTED)))
    doc=SimpleDocTemplate(str(PDF),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=17*mm,bottomMargin=21*mm,title='Evolutionary Algorithms for Exam Timetabling',author='Project Documentation')
    story=[]
    story += [Spacer(1,20*mm),Paragraph('PROJECT REPORT',ParagraphStyle('k',parent=styles['Normal'],fontName='Helvetica-Bold',fontSize=10,textColor=colors.HexColor('#'+BLUE),spaceAfter=12)),Paragraph('Evolutionary Algorithms<br/>for Exam Timetabling',styles['CoverTitle']),Paragraph('A prototype that generates semester-end examination schedules and compares GA, ES, and EP.',styles['Deck']),Spacer(1,15*mm)]
    coverdata=[[Paragraph('<b>Problem</b><br/>Multi-branch exam scheduling',styles['BodyX']),Paragraph('<b>Search methods</b><br/>GA · ES · EP',styles['BodyX'])],[Paragraph('<b>Demo data</b><br/>1,800 synthetic students',styles['BodyX']),Paragraph('<b>Output</b><br/>Calendar timetable + comparison dashboard',styles['BodyX'])]]
    t=Table(coverdata,colWidths=[80*mm,80*mm],rowHeights=[25*mm,25*mm]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#F2F5FA')),('BOX',(0,0),(-1,-1),.5,colors.HexColor('#DCE3EE')),('INNERGRID',(0,0),(-1,-1),.5,colors.HexColor('#DCE3EE')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10)]));story += [t,Spacer(1,12*mm),Paragraph('<b>Data note:</b> Course names, enrollment links, and USNs are fabricated for demonstration. The results are not an official college timetable.',styles['BodyX']),PageBreak()]

    story += [SectionBar('1. Problem statement'),Spacer(1,4*mm),Paragraph('The project assigns each exam paper to a date and session, then allocates enough halls for its enrolled students. The schedule must avoid simultaneous exams for the same student and fit within the available rooms. Among feasible schedules, the optimizer aims to reduce back-to-back papers and distribute enrollment more evenly.',styles['BodyX']),Paragraph('<b>Hard constraints</b>',styles['Heading3']),Paragraph('• A student cannot take two papers in the same session.<br/>• Total hall demand in a session cannot exceed 40 rooms.<br/>• A room is modeled with 60 seats; large exams can use multiple rooms.',styles['BodyX']),Paragraph('<b>Soft objectives</b>',styles['Heading3']),Paragraph('• Minimize student exam pairs in consecutive sessions.<br/>• Reduce variation in total enrolled exam seats across sessions.',styles['BodyX']),Spacer(1,4*mm),SectionBar('2. Data and assumptions'),Spacer(1,4*mm)]
    branchrows=[["Branch","Code","Synthetic students"]]+[[n,k,v] for k,(n,v) in {"CS":("Core CSE",600),"AM":("AI & ML",240),"AD":("AI & Data Science",240),"CB":("CS & Business Systems",240),"IS":("Information Science",240),"CI":("CS & IoT",240)}.items()]
    t=Table(branchrows,colWidths=[78*mm,30*mm,55*mm],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#'+NAVY)),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),8.5),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F2F5FA')]),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#DCE3EE')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story += [t,Spacer(1,3*mm),Paragraph('The demonstration generates 73 exam entries for Semesters III–VIII. Students receive synthetic identifiers such as 1BM23CS001. The example calendar uses weekdays only, with two periods each day: 08:00–09:30 and 12:00–13:30. Hall labels are 201–220 and 401–420.',styles['BodyX']),Paragraph('<b>Modeling caveat:</b> The current synthetic enrollment rule assumes students take all listed subjects for their branch and semester. Electives and actual cross-branch registrations require real enrollment data.',styles['BodyX']),PageBreak()]

    story += [SectionBar('3. Solution workflow'),Spacer(1,4*mm)]
    workflow=[('1','Create synthetic students and courses'),('2','Build a conflict graph from shared student enrollments'),('3','Encode one session assignment per exam'),('4','Repair student conflicts and room overloads'),('5','Score candidate schedules'),('6','Compare GA, ES, and EP'),('7','Export CSV/JSON and display dashboard')]
    for n,txt in workflow:
        row=Table([[Paragraph(f'<b>{n}</b>',styles['BodyX']),Paragraph(txt,styles['BodyX'])]],colWidths=[13*mm,150*mm]);row.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),colors.HexColor('#E8EEFF')),('BOX',(0,0),(-1,-1),.4,colors.HexColor('#DCE3EE')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]));story += [row,Spacer(1,2*mm)]
    story += [Spacer(1,4*mm),SectionBar('4. Fitness function'),Spacer(1,3*mm),Paragraph('<b>Penalty = 1,000,000 × clashes + 1,000,000 × hall overflow + 100 × back-to-back pairs + load imbalance</b>',styles['BodyX'])]
    metricrows=[["Metric","Definition","Weight / target"],["Student clashes","Conflicting exam pairs for the same student in the same session","1,000,000; target 0"],["Hall overflow","Number of halls needed beyond the 40 available in a session","1,000,000; target 0"],["Back-to-back pairs","Student exam pairs scheduled in consecutive session numbers","100; minimize"],["Load imbalance","Variance-like penalty across session enrollment totals","1; minimize"]]
    t=Table(metricrows,colWidths=[38*mm,91*mm,34*mm],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#'+NAVY)),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('LEADING',(0,0),(-1,-1),10),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F2F5FA')]),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#DCE3EE')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story += [t,Spacer(1,3*mm),Paragraph('<b>Winner rule:</b> The program ranks feasibility first, then back-to-back pairs, then load imbalance. This lexicographic ranking can select a different algorithm than sorting only by the weighted total penalty.',styles['BodyX']),PageBreak()]

    story += [SectionBar('5. Algorithms compared'),Spacer(1,4*mm)]
    algrows=[["Method","Candidate variation","Selection"],["Genetic Algorithm (GA)","Uniform crossover between two parent schedules; mutation moves or swaps exams","Tournament-like parent choice; elites retained"],["Evolution Strategy (ES)","Mutation of parent schedules","(μ + λ) survivor selection"],["Evolutionary Programming (EP)","Mutation of each parent schedule","Pairwise competition among parents and offspring"]]
    t=Table(algrows,colWidths=[42*mm,76*mm,47*mm],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#'+NAVY)),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('LEADING',(0,0),(-1,-1),10),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F2F5FA')]),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#DCE3EE')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story += [t,Spacer(1,4*mm),Paragraph('These are educational variants. Evolutionary algorithms are stochastic search methods; there is no universally best method for every timetable. Results depend on the representation, operators, constraints, data, seed, and runtime budget.',styles['BodyX']),SectionBar('6. Demonstration results'),Spacer(1,3*mm)]
    comp=[["Algorithm","Score","Clashes","Hall over.","Back-to-back","Load imbalance","Time"]]
    for r in DATA['comparison']: comp.append([r['algorithm'],f"{r['fitness']:,}",str(r['hard_conflicts']),str(r['room_overflow']),f"{r['back_to_back_pairs']:,}",f"{r['load_imbalance']:,}",f"{r['runtime_seconds']:.3f}s"])
    t=Table(comp,colWidths=[24*mm,25*mm,20*mm,22*mm,27*mm,27*mm,20*mm],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#'+NAVY)),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),7.5),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F2F5FA')]),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#DCE3EE')),('ALIGN',(1,1),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story += [t,Spacer(1,3*mm)]
    best=next(r for r in DATA['comparison'] if r['algorithm']==DATA['best_algorithm'])
    story += [Paragraph(f"<b>Observed winner:</b> {DATA['best_algorithm']} by feasibility-first ranking, with {best['back_to_back_pairs']:,} back-to-back pairs. All three methods had zero hard conflicts and zero hall overflow in this run.",styles['BodyX']),Paragraph(f"Run configuration: {DATA['students']:,} synthetic students; {DATA['exams']} exam entries; {DATA['sessions']} sessions; population {DATA['population']}; {DATA['generations']} generations; seed {DATA['seed']}; dates {DATA['start_date']} to {DATA['end_date']}.",styles['SmallX']),PageBreak()]

    story += [SectionBar('7. Technology stack and modules'),Spacer(1,4*mm)]
    tech=[["Component","Technology","Responsibility"],["Optimization engine","Python 3 standard library","Dataset, conflict graph, GA/ES/EP operators, repair, scoring, room assignment"],["Local API","Python http.server","Serves the page and runs the optimizer from dashboard inputs"],["Front end","HTML, CSS, JavaScript","Neumorphic UI, calendar range, semester tables, controls, result cards"],["Charts","HTML Canvas API","Fitness-component and session-load charts"],["Data output","CSV and JSON","Timetable rows, algorithm metrics, run settings and dates"]]
    t=Table(tech,colWidths=[35*mm,46*mm,84*mm],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#'+NAVY)),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('LEADING',(0,0),(-1,-1),10),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F2F5FA')]),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#DCE3EE')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story += [t,Spacer(1,4*mm),Paragraph('<b>Project files:</b> main.py (generator and algorithms), app.py (local web server), dashboard.html (user interface), output/timetable.csv, output/algorithm_comparison.csv, and output/run_summary.json.',styles['BodyX']),SectionBar('8. Limitations and next steps'),Spacer(1,3*mm),Paragraph('• Replace fabricated enrollment and course lists with verified registrar data.<br/>• Model holidays, room availability by period, exam duration, accommodations, and invigilator availability.<br/>• Improve elective enrollment representation and add validation against actual student registrations.<br/>• Compare algorithms across repeated seeds and equal compute budgets; report averages and spread.<br/>• Calibrate penalty weights with academic scheduling stakeholders and manually validate the final timetable.',styles['BodyX']),Paragraph('<b>Conclusion:</b> The prototype demonstrates how evolutionary search can generate and compare feasible exam timetables. Its current output is a teaching/demo artifact, not an official schedule.',styles['BodyX'])]
    doc.build(story,onFirstPage=draw_footer,onLaterPages=draw_footer)

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    build_pptx();build_pdf()
    print(PPTX);print(PDF)
