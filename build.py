import html, re, math, sys

OUT = sys.argv[1]
def esc(s): return html.escape(s, quote=True)
SUP = str.maketrans('0123456789n', '⁰¹²³⁴⁵⁶⁷⁸⁹ⁿ')
def plain(t):  # KaTeX가 없을 때 보일 대체 텍스트
    def frac(m):
        wrap = lambda s: s if re.fullmatch(r'[\w.]+', s) else f'({s})'
        return f'{wrap(m.group(1))}/{wrap(m.group(2))}'
    t = re.sub(r'\\d?frac\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*)\}', frac, t)
    for a, b in [('\\cdots','⋯'),('n\\log_2','n log₂'),('n\\log','n log'),('\\times','×'),('\\cdot','·'),('\\le','≤'),('\\ge','≥'),('\\rightarrow','→'),('\\approx','≈'),
                 ('\\log_2','log₂'),('\\log','log'),('\\;',' '),('\\,',' '),('n_0','n₀'),('T_A(n)','A의 T(n)'),('T_B(n)','B의 T(n)'),('T_A(10)','A의 T(10)'),('T_B(10)','B의 T(10)')]:
        t = t.replace(a, b)
    t = re.sub(r'\^\{([0-9n]+)\}', lambda m: m.group(1).translate(SUP), t)
    t = re.sub(r'\^([0-9n])', lambda m: m.group(1).translate(SUP), t)
    return t.replace('{', '').replace('}', '').replace('<', '<')
def M(tex, fb=None):
    return f'<span data-math="{esc(tex)}">{esc(fb if fb is not None else plain(tex))}</span>'

KW = r'\b(for|in|if|and|def|return|print|range|while|len)\b'
def hl(src):
    s = esc(src)
    s = re.sub(KW, r'<b>\1</b>', s)
    return s.replace('⟦', '<mark>').replace('⟧', '</mark>')

def code(lines, id=None, cls='', label=None, legend=True):
    out = []
    for k, item in enumerate(lines, 1):
        src, cnt = item[0], item[1]
        fl = item[2] if len(item) > 2 else ''
        c = ''
        if cnt is not None:
            if 'h' in fl:
                c = f'<span class="cnt"><span class="cnt-q"># ?</span><span class="cnt-a"># {esc(cnt)}</span></span>'
            elif 'm' in fl:
                c = f'<span class="cnt none"># {esc(cnt)}</span>'
            else:
                c = f'<span class="cnt"># {esc(cnt)}</span>'
        focus = ' focus' if 'f' in fl else ''
        out.append(f'<span class="line{focus}"><i>{k}</i><span class="src">{hl(src)}</span>{c}</span>')
    lab = ''
    if label:
        lg = f'<span class="legend">{legend if isinstance(legend, str) else "# = 실행 횟수"}</span>' if legend else ''
        lab = f'<div class="code-label"><span>{label}</span>{lg}</div>'
    idattr = f' id="{id}"' if id else ''
    return f'<div class="code-block">{lab}<pre class="code {cls}"{idattr}><code>{"".join(out)}</code></pre></div>'

def answer(qid, inner, label='정답·해설 보기'):
    return (f'<button class="answer-toggle" type="button" aria-expanded="false" aria-controls="{qid}">{label}</button>'
            f'<div class="answer-slot"><div id="{qid}" hidden>{inner}</div></div>')

def AQ(q, a):  # 정답 공개 전 '?' / 공개 후 a
    return f'<span class="ans-q">{q}</span><span class="ans-a">{a}</span>'

LESSON = {1: '1차시 · 실행 횟수 세기', 2: '2차시 · 빅오와 증가율', 3: '선택 3차시 · 삼각형 실습'}
slides = []
def slide(title, body, cls='', lesson=1, raw_title=False):
    n = len(slides) + 1
    head = title if raw_title else f'<h2 class="reveal" id="title-{n}">{title}</h2>'
    slides.append(
        f'<section class="slide {cls}" id="slide-{n}" data-lesson="{lesson}" aria-labelledby="title-{n}">\n'
        f'{head}\n{body}\n'
        f'<footer><span class="lesson-tag">{LESSON[lesson]}</span><span class="page-number">{n:02d} / TOTAL</span></footer>\n</section>')

# ---------- 그래프 ----------
CHARTS = {
 'A': dict(max=20, ymax=850, ticks=[0,200,400,600,800], xt=[0,5,10,15,20], unit='실행 횟수(회)',
           labels=['2n+2','2n²+n+2'], f=[lambda n:2*n+2, lambda n:2*n*n+n+2]),
 'D': dict(max=20, ymax=420, ticks=[0,100,200,300,400], xt=[0,5,10,15,20], unit='함수 값',
           labels=['n','n²'], f=[lambda n:n, lambda n:n*n]),
 'B': dict(max=32, ymax=170, ticks=[0,40,80,120,160], xt=[0,8,16,24,32], unit='함수 값',
           labels=['1','log₂n','n','n log₂n'], f=[lambda n:1, lambda n:math.log2(n), lambda n:n, lambda n:n*math.log2(n)]),
 'C': dict(max=10, ymax=1100, ticks=[0,250,500,750,1000], xt=[0,2,4,6,8,10], unit='함수 값',
           labels=['n²','n³','2ⁿ'], f=[lambda n:n*n, lambda n:n**3, lambda n:2**n]),
}
FCOL = {'fc-1':'#5d6879','fc-log':'#744ca0','fc-n':'#3156d3','fc-nlog':'#a86b00','fc-n2':'#c84b35','fc-n3':'#9c2f7a','fc-2n':'#2f3b52'}
DASH = {'fc-1':'2 5','fc-log':'12 4 2 4','fc-n':'none','fc-nlog':'9 6','fc-n2':'none','fc-n3':'4 4','fc-2n':'14 6'}
X0, X1 = 80, 780
def fmt(v):
    v = round(v, 2)
    return f'{int(v):,}' if v == int(v) else f'{v:,}'

def static_chart(k, fcs):
    # 축·눈금·격자는 여기서 한 번만 그린다. slides.js는 곡선(.static-curves)만 지우고 다시 그린다.
    c = CHARTS[k]; X = lambda n: X0 + n / c['max'] * (X1 - X0); Y = lambda v: 380 - v / c['ymax'] * 320
    a = [f'<text x="{X0}" y="28" class="axis-label">{c["unit"]}</text>',
         f'<text x="{X1}" y="444" text-anchor="end" class="axis-label">입력 크기 n</text>']
    for t in c['ticks']:
        a.append(f'<line x1="{X0}" x2="{X1}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="#e0e6ef"/>')
        a.append(f'<text x="66" y="{Y(t)+7:.1f}" text-anchor="end" class="tick-label">{t}</text>')
    for t in c['xt']: a.append(f'<text x="{X(t):.1f}" y="412" text-anchor="middle" class="tick-label">{t}</text>')
    a.append(f'<line x1="{X0}" x2="{X1}" y1="380" y2="380" stroke="#8391a5"/>')
    p = []
    used = []
    for i, f in enumerate(c['f']):
        d = ' '.join(f'{"L" if j else "M"}{X(j+1):.1f},{Y(f(j+1)):.1f}' for j in range(c['max']))
        p.append(f'<path d="{d}" fill="none" stroke="{FCOL[fcs[i]]}" stroke-width="4" stroke-dasharray="{DASH[fcs[i]]}"/>')
        ly = min(375, max(50, Y(f(c['max'])) + 7))
        while any(abs(u - ly) < 24 for u in used): ly -= 25
        used.append(ly)
        p.append(f'<text x="{X(c["max"])+14:.1f}" y="{ly:.1f}" class="line-label" fill="{FCOL[fcs[i]]}">{c["labels"][i]}</text>')
    return '<g class="axes">' + ''.join(a) + '</g><g class="static-curves">' + ''.join(p) + '</g>'

def graph(k, values, unit=''):  # values: [(TeX, 대체 텍스트, 색 클래스)]
    c = CHARTS[k]; fcs = [v[2] for v in values]
    final = ', '.join(f'{lab} = {fmt(c["f"][i](c["max"]))}' for i, lab in enumerate(c['labels']))
    vals = ''.join(
        f'<div class="live-value {fc}"><span>{M(tex, fb)}</span><strong><span data-value="{i}">{fmt(c["f"][i](c["max"]))}</span><small>{unit}</small></strong></div>'
        for i, (tex, fb, fc) in enumerate(values))
    data = f'data-chart="{k}" data-max="{c["max"]}" data-ymax="{c["ymax"]}" data-labels="{esc("|".join(c["labels"]))}"'
    return (f'<div class="graph-component" {data}><div class="graph-layout">'
            f'<div class="graph-wrap"><svg viewBox="0 0 900 450" role="img" aria-label="입력 크기 n을 1부터 {c["max"]}까지 늘린 {c["unit"]} 그래프. n = {c["max"]}일 때 {final}">{static_chart(k, fcs)}</svg></div>'
            f'<aside class="graph-values"><div class="n-display">입력 크기 <strong>n = <span data-n>{c["max"]}</span></strong></div>{vals}'
            f'<button class="play" type="button">그래프 재생</button><p class="small">재생하면 n = 1부터 다시 그린다.</p></aside></div></div>')

# =========================================================
# 1차시
# =========================================================
slide('', f'''<div class="cover-layout">
 <div class="reveal"><p class="eyebrow">정보과학 · 알고리즘의 성능과 분석 <span>교과서 156~169쪽</span></p><h1 id="title-1">같은 답.<br>그런데<br><em>다른 속도?</em></h1>
  <p class="lead">두 방법 모두 결과는 100이다.<br>그렇다면 컴퓨터가 하는 일의 양도 같을까?</p>
  <p class="hand note">코드 길이가 아니라, 실행 횟수를 보자!</p></div>
 <div class="reveal">
  <div class="sum-row"><span class="pill">방법 A</span><span>0에 10을 10번 더하기</span><strong>덧셈 10번</strong></div>
  <div class="sum-row coral"><span class="pill coral">방법 B</span><span>0에 1을 100번 더하기</span><strong>덧셈 100번</strong></div>
  <p class="same">결과는 똑같이 100.<br>그런데 덧셈 횟수는 <b>10배</b> 차이 난다.</p></div>
</div>''', cls='cover', raw_title=True)

slide('알고리즘의 효율, <em>무엇으로</em> 비교할까?', f'''<div class="lesson-content reveal">
<p class="goal"><b>1차시 목표</b>코드의 줄별 실행 횟수를 세어 실행 횟수 식 T(n)으로 나타내고, n이 커질 때 비교할 수 있다.</p>
<div class="split">
 <div class="concept"><span>시간 복잡도 · 이번 단원의 중심</span><h3>일을 얼마나 많이 할까?</h3>
  <p class="body-text">입력이 커질 때, 명령이<br><strong>몇 번 실행되는지</strong> 살펴본다.</p></div>
 <div class="concept purple"><span>공간 복잡도</span><h3>메모리를 얼마나 쓸까?</h3>
  <p class="body-text">입력이 커질 때, 필요한<br><strong>저장 공간</strong>이 얼마인지 살펴본다.</p></div>
</div>
<div class="callout"><b>왜 ‘시간(초)’이 아니라 ‘횟수’일까?</b> 같은 코드도 컴퓨터 성능에 따라 걸리는 시간이 다르다.<br>
그래서 컴퓨터와 상관없는 <b>명령의 실행 횟수</b>로 비교한다.<br>
<b>입력 크기 {M("n","n")}</b>: 처리할 데이터의 양. 이 수업의 예제에서는 반복 횟수를 정하는 수다.</div>
</div>''')

slide('안쪽 한 줄은 <em>몇 번</em> 실행될까?', f'''<div class="split center reveal">
<div>{code([("ans = 0","1회"),("for i in range(⟦3⟧):","3회"),("    for j in range(⟦3⟧):","3×3 = 9회"),("        ans = ans + 1","3×3 = 9회","f")], label="입력 크기 n = 3일 때")}
 <p class="code-note"><b>for 줄</b>은 한 바퀴 돌 때마다 1회로 센다. 그래서 안쪽 for 줄도 9회다.</p>
 <p class="body-text">바깥 반복(i)이 <strong>한 번</strong> 돌 때마다<br>안쪽 반복(j)은 처음부터 끝까지 <strong>3번</strong> 돈다.</p></div>
<div class="grid-explain"><p class="grid-caption">4번 줄이 실행될 때마다 칸을 하나씩 채우면</p>
 <div class="grid-label"><span>j →</span><span>0</span><span>1</span><span>2</span></div>
 <div class="count-grid"><span class="row-label">i = 0</span><b>1</b><b>2</b><b>3</b><span class="row-label">i = 1</span><b>4</b><b>5</b><b>6</b><span class="row-label">i = 2</span><b>7</b><b>8</b><b>9</b></div>
 <p class="equation">{M("3 \\times 3 = 9")}회</p><p class="hand">n번씩 n묶음 → n × n = n²회</p></div>
</div>''')

slide('두 반복을 <em>곱해서</em> 설명해 보자.', f'''<div class="lesson-content reveal"><div class="split">
<div>{code([("for i in range(4):","4회","h"),("    for j in range(4):","16회","h"),("        print(i, j)","16회","fh")], label="주석의 ?는 정답을 열면 나타난다")}
 <p class="hand note">혼자 생각 → 짝에게 이유 설명하기!</p></div>
<div><span class="quiz-tag">Q1</span>
 <ol class="question"><li>3번 줄(print)은 몇 번 실행될까?</li><li>2번 줄을 <code>range(3)</code>으로 바꾸면,<br>3번 줄은 몇 번 실행될까?</li></ol>
 {answer("q1", f'<div class="answer-equation">① {M("4\\times4=16")}회 &nbsp;② {M("4\\times3=12")}회</div><p class="body-text">바깥 반복 1번마다 안쪽 반복이 처음부터 끝까지 돈다.<br>그래서 4 + 4가 아니라 <strong>4묶음 × 4번</strong>이다.</p>')}</div>
</div></div>''', cls='quiz')

def sum_block(color, tsum, tfinal, n10, n10calc):
    return (f'<p class="sum-line">줄별 횟수를 모두 더하면 {M(tsum)}</p>'
            f'<p class="formula {color}">{M(tfinal)}</p>'
            f'<p class="result">n = 10이면 {M(n10calc)} → <strong>{n10}회</strong></p>')

slide('결과는 같아도, <em>해야 할 일은 다르다.</em>', f'''<div class="lesson-content reveal"><div class="compare">
<article><div class="compare-head"><span class="pill">A</span><h3>n을 n번 더하기</h3></div>
 {code([("def sum_a(n):","세지 않음","m"),("    ans = 0","1회"),("    for i in range(n):","n회"),("        ans = ans + n","n회","f"),("    return ans","1회")], cls="sm")}
 {sum_block("blue","1 + n + n + 1","T_A(n) = 2n + 2","22","2\\times10+2")}</article>
<article><div class="compare-head"><span class="pill coral">B</span><h3>1을 n²번 더하기</h3></div>
 {code([("def sum_b(n):","세지 않음","m"),("    ans = 0","1회"),("    for i in range(n):","n회"),("        for j in range(n):","n²회"),("            ans = ans + 1","n²회","f"),("    return ans","1회")], cls="sm coral")}
 {sum_block("coral-text","1 + n + n^2 + n^2 + 1","T_B(n) = 2n^2 + n + 2","212","2\\times100+10+2")}</article>
</div>
<div class="callout"><b>세는 기준(교과서)</b> &nbsp;대입·반환은 1회 · for 줄은 한 바퀴마다 1회 · 함수 이름을 정하는 def 줄은 세지 않는다.</div></div>''')

slide('n = 5를 넣어 <em>직접 계산해 보자.</em>', f'''<div class="lesson-content reveal"><div class="split">
<div><p class="formula blue">{M("T_A(n)=2n+2")}</p><p class="formula coral-text">{M("T_B(n)=2n^2+n+2")}</p>
 <p class="hand note">결과 값과 실행 횟수, 같은 말일까?</p>
 <div class="callout">교과서의 세는 기준을 따른다. Python 내부의 일(반복 종료 확인 등)은 세지 않는다. <b>기준을 하나로 정해 두 코드에 똑같이 적용하면</b> 공정하게 비교할 수 있다.</div></div>
<div><span class="quiz-tag">Q2</span>
 <ol class="question"><li>n = 5일 때, 두 코드는 각각 몇 번 실행될까?</li><li>실행 횟수가 다르면,<br>두 코드가 구한 결과 값도 다를까?</li></ol>
 {answer("q2", f'<div class="answer-equation">A: {M("2\\times5+2=12")}회<br>B: {M("2\\times25+5+2=57")}회</div><p class="body-text">두 코드가 구한 값은 모두 25(= 5²)로 같다. n = 10이면 둘 다 100.<br><strong>결과 값</strong>(무엇을 구했나)과 <strong>실행 횟수</strong>(얼마나 일했나)는 다른 것이다.</p>')}</div>
</div></div>''', cls='quiz')

slide('n이 커질수록, <em>차이는 더 크게 벌어진다.</em>', f'''<div class="lesson-content reveal">
{graph("A", [("2n+2",None,"fc-n"),("2n^2+n+2",None,"fc-n2")], "회")}
<div class="graph-takeaway"><p class="hand note">n이 2배가 되면?</p>
 <p class="body-text">n = 10 → 20일 때 &nbsp;<span class="fc-n">2n+2: 22 → 42회 (약 1.9배)</span> · <span class="fc-n2">2n²+n+2: 212 → 822회 (약 3.9배)</span><br>n이 클수록 각각 2배, 4배에 점점 가까워진다.</p></div>
</div>''', cls='graph-slide')

slide('입력이 10배가 되면, <em>일도 10배일까?</em>', f'''<div class="lesson-content reveal">
<table class="lesson-table"><thead><tr><th>함수</th><th class="num">n = 10</th><th class="num">n = 100</th><th class="num">몇 배?</th></tr></thead>
<tbody><tr><td>{M("n")}</td><td class="num">10</td><td class="num">100</td><td class="num">{AQ("?","10배")}</td></tr>
<tr><td>{M("n^2")}</td><td class="num">100</td><td class="num">10,000</td><td class="num">{AQ("?","100배")}</td></tr></tbody></table>
<div class="split"><div><span class="quiz-tag">Q3</span><p class="question">n이 10배가 되면,<br>각 함수의 값은 몇 배가 될까?</p></div>
<div>{answer("q3", f'<div class="answer-equation">{M("n")}: 10배 &nbsp;/ &nbsp;{M("n^2")}: {M("10\\times10=100")}배</div><p class="body-text">n²은 n을 두 번 곱한 값이라, 입력이 10배면 값은 10² = 100배가 된다.<br>실행 횟수가 n²인 코드는 입력이 커질 때 훨씬 빨리 느려진다.</p><p class="small">2n + 2처럼 계수·상수가 붙은 식은 정확히 10배는 아니지만, n이 클수록 그 배율에 가까워진다.</p>')}</div></div>
</div>''', cls='quiz')

slide('지금까지 센 것을 <em>용어로 정리하자.</em>', f'''<div class="lesson-content reveal">
<dl class="term-list">
 <dt>입력 크기 {M("n")}</dt><dd>코드가 처리할 데이터의 양. 예제에서는 반복 횟수를 정한다.</dd><dd class="ex">range(n)</dd>
 <dt>한 줄의 실행 횟수</dt><dd>특정한 <b>한 줄</b>이 실행된 횟수</dd><dd class="ex">안쪽 줄: {M("n^2")}회</dd>
 <dt>총 실행 횟수 {M("T(n)")}</dt><dd><b>모든 줄</b>의 실행 횟수를 더한 것</dd><dd class="ex">{M("2n^2+n+2")}</dd>
</dl>
<p class="hand note">“몇 번?”이라고 물으면, 한 줄인지 전체인지 먼저 확인!</p>
<details class="optional"><summary>시간이 남으면 · 피보나치 예제로 연습하기</summary><div class="split center">
 {code([("def fibonacci(n):","세지 않음","m"),("    f1 = 1","1회"),("    f2 = 1","1회"),("    for i in range(3, n + 1):","n−2회"),("        temp = f1 + f2","n−2회"),("        f1 = f2","n−2회"),("        f2 = temp","n−2회"),("    return f2","1회")], cls="sm", label="n ≥ 2일 때")}
 <div><p class="body-text"><code>range(3, n + 1)</code>은 3, 4, …, n이므로<br><strong>n − 2번</strong> 반복한다.</p>
  <p class="formula">{M("T(n)=1+1+4(n-2)+1=4n-5")}</p>
  <p class="body-text">예: n = 10이면 4 × 10 − 5 = 35회</p></div>
</div></details></div>''')

slide('실행 횟수를 세는 <em>세 단계</em>', f'''<div class="lesson-content reveal"><div class="three-points">
<article><b>01</b><h3>범위 읽기</h3><p class="body-text">각 for가 몇 바퀴 도는지<br><code>range</code>를 보고 확인한다.</p></article>
<article><b>02</b><h3>줄마다 적기</h3><p class="body-text">줄 옆에 <span class="teal"># 1회</span>, <span class="teal"># n회</span>처럼<br>실행 횟수를 적는다.</p></article>
<article><b>03</b><h3>더해서 비교하기</h3><p class="body-text">모두 더한 T(n)으로<br>n이 커질 때 차이를 본다.</p></article>
</div><p class="hand note">다음 시간: 이 ‘커지는 방식’을 간단히 나타내 보자.</p></div>''', cls='bigo')

slide('1차시 마무리: <em>출구 질문</em>', f'''<div class="lesson-content reveal"><div class="split">
<div>{code([("for i in range(n):","n회","h"),("    for j in range(i):","0+1+⋯+(n−1)회","h"),("        print(i, j)","0+1+⋯+(n−1)회","fh")], label="안쪽 범위가 n이 아니라 i다")}
 <p class="hand note">안쪽은 매번 같은 횟수만큼 돌까?</p></div>
<div><span class="quiz-tag">출구 질문</span>
 <ol class="question"><li>n = 4일 때, 3번 줄은 몇 번 실행될까?</li><li>왜 4 × 4 = 16이 아닐까?</li></ol>
 {answer("exit1", f'<div class="answer-equation">n = 4 → {M("0+1+2+3=6")}회</div><p class="body-text">i = 0, 1, 2, 3일 때 안쪽 반복은 0, 1, 2, 3번 돈다. 안쪽 범위가 i에 따라 달라지므로 그냥 곱할 수 없다.</p><p class="small">일반적으로는 0 + 1 + ⋯ + (n−1) = n(n−1)/2회. 2차시 삽입 정렬에서 다시 만난다.</p>')}</div>
</div></div>''', cls='quiz')

# =========================================================
# 2차시
# =========================================================
L = 2
slide('정확한 횟수보다,<br><em>커지는 방식</em>을 보자.', f'''<div class="lesson-content reveal">
<p class="goal"><b>2차시 목표</b>실행 횟수를 빅오로 나타내고, 증가율로 알고리즘을 비교할 수 있다.</p>
<p class="body-text review"><b>복습</b> 지난 시간 B 코드는 {M("T(n)=2n^2+n+2")}. n = 20이면 몇 회일까? <button class="answer-toggle inline" type="button" aria-expanded="false" aria-controls="rev2">복습 정답 보기</button><span id="rev2" class="inline-answer" hidden>→ 2 × 400 + 20 + 2 = <b>822회</b></span></p>
<div class="split center">
<div><div class="hero-math">{M("n")}</div><p class="body-text">입력이 2배 → 값도 <strong>2배</strong></p></div>
<div><div class="hero-math coral-text">{M("n^2")}</div><p class="body-text">입력이 2배 → 값은 2² = <strong>4배</strong></p></div>
</div><p class="body-text mt">입력이 커질 때 값이 커지는 빠르기를 <strong>증가율</strong>이라고 한다.</p>
<p class="hand note">둘 다 커지지만, 커지는 빠르기가 다르다.</p></div>''', cls='cover', lesson=L)

slide('n이 커지면, <em>어떤 항이 결과를 좌우할까?</em>', f'''<div class="lesson-content reveal">
<p class="formula">{M("T(n)=n^2+2n+1")}</p>
<table class="lesson-table"><thead><tr><th>항</th><th class="num">n = 10일 때</th><th class="num">전체 중 비중</th><th class="num">n = 1,000일 때</th><th class="num">전체 중 비중</th></tr></thead><tbody>
<tr><td>{M("n^2")}</td><td class="num">100</td><td class="num">약 82.6%</td><td class="num">1,000,000</td><td class="num hl">약 99.8%</td></tr>
<tr><td>{M("2n")}</td><td class="num">20</td><td class="num">약 16.5%</td><td class="num">2,000</td><td class="num">약 0.2%</td></tr>
<tr><td>1</td><td class="num">1</td><td class="num">약 0.8%</td><td class="num">1</td><td class="num">약 0.0001%</td></tr>
<tr class="total"><td>합계</td><td class="num">121</td><td class="num">100%</td><td class="num">1,002,001</td><td class="num">100%</td></tr></tbody></table>
<p class="hand note">n이 커질수록 최고차항 n²이 거의 전부를 차지한다.</p>
<p class="body-text">그래서 증가율을 볼 때는 <strong>최고차항만 남기고, 계수도 뗀다.</strong> 단, n이 작을 때는 나머지 항도 무시할 만큼 작지 않다.</p>
</div>''', lesson=L)

slide('빅오(O): 증가율의 <em>상한</em>을 나타내는 기호', f'''<div class="lesson-content reveal"><div class="bigo-layout"><div>
<p class="definition">n이 충분히 클 때, T(n)이 어떤 함수 g(n)의<br><strong>상수배를 넘지 않으면</strong> T(n)은 O(g(n))이다.</p>
<p class="body-text">예: 2n + 2는 n ≥ 1이면 <strong>4n(n의 4배)</strong>을 넘지 않는다.<br>그래서 2n + 2는 <strong>O(n)</strong>이다.</p>
<details class="optional"><summary>더 알아보기 · 빅오의 정확한 뜻</summary>
<div class="bound">{M("T(n) \\le c \\cdot g(n)")}<span class="bound-condition">{M("n \\ge n_0")}일 때 항상 성립하는 상수 c, n₀가 있으면 T(n)은 O(g(n))</span></div>
<svg class="bound-chart" viewBox="0 0 440 160" role="img" aria-label="n이 1 이상일 때 2n+2는 4n 이하"><path d="M30 130H390 M30 130V15" stroke="#829c93" fill="none"/><path d="M65 110L340 22" stroke="#007f73" stroke-width="4" fill="none"/><path d="M65 110L340 66" stroke="#3156d3" stroke-width="4" fill="none"/><text x="349" y="27">4n</text><text x="349" y="72">2n+2</text><text x="57" y="150">1</text><text x="395" y="137">n</text></svg>
<div class="cn-tags"><span>g(n) = n</span><span>c = 4</span><span>n₀ = 1</span></div></details></div>
<div class="notation"><span class="notation-label">선형 증가의 상한</span><strong>{M("O(n)")}</strong>
<div class="hand note">‘정확히 n번’이라는 뜻이 아니야!</div>
<p>{M("2n+2 \\;\\rightarrow\\; O(n)")}<br>{M("2n^2+n+2 \\;\\rightarrow\\; O(n^2)")}</p></div>
</div></div>''', cls='bigo', lesson=L)

slide('빅오로 <em>나타내 보자.</em>', f'''<div class="lesson-content reveal"><div class="split">
<div><div class="formula-list big"><p>① {M("n^2+2n+1")}</p><p>② {M("5n+2")}</p><p>③ {M("2")}</p></div></div>
<div><span class="quiz-tag">Q4</span>
 <p class="question">가장 빨리 커지는 항만 남기고,<br>계수를 떼어 빅오로 나타내 보자.</p>
 {answer("q4", f'<div class="answer-equation">① {M("O(n^2)")} &nbsp;② {M("O(n)")} &nbsp;③ {M("O(1)")}</div><p class="body-text">① n²이 가장 빨리 커진다.<br>② 5n에서 계수 5를 뗀다.<br>③ n과 상관없이 늘 같다 → 상수 시간 O(1)</p>')}</div>
</div></div>''', cls='quiz', lesson=L)

slide('증가율을 <em>그래프로 확인하자.</em>', f'''<div class="lesson-content reveal">
{graph("D", [("n",None,"fc-n"),("n^2",None,"fc-n2")])}
<div class="graph-takeaway"><p class="hand note">n이 2배가 되면?</p>
 <p class="body-text">n = 10 → 20일 때 &nbsp;<span class="fc-n">n: 10 → 20 (2배)</span> · <span class="fc-n2">n²: 100 → 400 (4배)</span></p></div>
<details class="optional"><summary>선택 확장 · 로그와 지수의 증가율</summary>
 <h3>반으로 몇 번 나누면 1이 될까?</h3>
 <p class="body-text">32 → 16 → 8 → 4 → 2 → 1: 5번. 이 횟수가 log₂32 = 5이다.<br>log₂n은 n이 커져도 아주 천천히 커진다. <strong>예측:</strong> n과 n log₂n 중 어느 쪽이 더 빨리 커질까?</p>
 {graph("B", [("1",None,"fc-1"),("\\log_2 n",None,"fc-log"),("n",None,"fc-n"),("n\\log_2 n",None,"fc-nlog")])}
 <p class="body-text">관찰: n = 32일 때 n은 32, n log₂n은 160으로 이미 5배다. n log₂n은 n보다 빨리 커지지만, n²(1,024)보다는 훨씬 느리다.</p>
 <h3>작은 n에서 본 순서가 끝까지 유지될까?</h3>
 {graph("C", [("n^2",None,"fc-n2"),("n^3",None,"fc-n3"),("2^n",None,"fc-2n")])}
 <table class="lesson-table"><thead><tr><th>n</th><th class="num">{M("n^3")}</th><th class="num">{M("2^n")}</th></tr></thead><tbody><tr><td>5</td><td class="num">125</td><td class="num">32</td></tr><tr><td>10</td><td class="num">1,000</td><td class="num">1,024</td></tr><tr><td>20</td><td class="num">8,000</td><td class="num hl">1,048,576</td></tr></tbody></table>
 <p class="body-text">n = 2~9에서는 n³이 더 크지만, n = 10부터 2ⁿ이 앞지르고 차이가 걷잡을 수 없이 커진다.<br>그래프 몇 개만 보고 ‘항상 크다’고 결론 내릴 수는 없다. 수학적 근거가 필요하다.</p>
</details></div>''', cls='graph-slide', lesson=L)

rows = [("1","O(1)","상수",["1","1","1","1"]),
        ("n","O(n)","선형",["10","100","1,000","10,000"]),
        ("n\\log_2 n","O(n\\log n)","선형 로그",["약 33","약 664","약 9,966","약 132,877"]),
        ("n^2","O(n^2)","이차",["100","10,000","1,000,000","100,000,000"]),
        ("2^n","O(2^n)","지수",["1,024","≈ 1.27×10<sup>30</sup>","≈ 1.07×10<sup>301</sup>","≈ 2.00×10<sup>3010</sup>"])]
FCLS = {'1':'fc-1','n':'fc-n','n\\log_2 n':'fc-nlog','n^2':'fc-n2','2^n':'fc-2n'}
trs = ''.join(f'<tr class="{FCLS[f]}"><th>{M(f)} <small>{name} · {M(o)}</small></th>' + ''.join(f'<td>{v}</td>' for v in vals) + '</tr>' for f,o,name,vals in rows)
slide('입력이 커지면, 차이는 <em>이만큼</em> 벌어진다.', f'''<div class="lesson-content reveal"><p class="swipe-hint">← 표를 옆으로 밀어 보기</p><div class="complexity-scroll">
<table class="complexity-table"><thead><tr><th>대표 함수</th><th>n = 10</th><th>n = 100</th><th>n = 1,000</th><th>n = 10,000</th></tr></thead><tbody>{trs}</tbody></table></div>
<p class="ask-row"><span class="hand note">입력은 10배씩. 일은 몇 배씩 늘어날까?</span><button class="answer-toggle inline" type="button" aria-expanded="false" aria-controls="tbl-ans">정답 보기</button><span id="tbl-ans" class="inline-answer" hidden>n: 10배 · n log n: 10배보다 더(이 표에서 13~20배) · n²: 100배 · 2ⁿ: 비교할 수 없을 만큼</span></p>
<div class="callout"><b>1초에 1억(10⁸) 번 계산하는 컴퓨터라면?</b> n = 10,000일 때 n²은 약 1초, n log₂n은 약 0.001초면 끝난다.<br>하지만 n = 100일 때 2ⁿ은 약 4 × 10¹⁴년, 우주 나이의 약 3만 배가 걸린다.</div>
<p class="caption">표의 값은 대표 함수의 값이며 실제 실행 시간이 아니다. 큰 값은 반올림했다.<br>빅오에서는 로그의 밑을 생략해 O(n log n)으로 쓴다. 밑이 달라져도 상수배 차이일 뿐이기 때문이다.</p>
</div>''', cls='complexity-static', lesson=L)

slide('반복문이 두 개면, <em>항상 n²번</em>일까?', f'''<div class="lesson-content reveal"><div class="split">
<div>{code([("n = 4","1회","h"),("for i in range(n):","n회","h"),("    for j in range(⟦3⟧):","3n회","h"),("        print(i, j)","3n회","fh")], label="n은 입력 크기 · ?는 정답을 열면 나타난다")}
 <p class="hand note">반복문 개수 말고, 반복 범위를 보자!</p></div>
<div><span class="quiz-tag">Q5</span>
 <ol class="question"><li>n = 4일 때, 4번 줄은 몇 번 실행될까?</li><li>일반적인 n이라면 몇 번일까?<br>빅오로 나타내면?</li><li>그렇게 생각한 이유는?</li></ol>
 {answer("q5", f'<div class="answer-equation">n = 4 → {M("4\\times3=12")}회<br>일반: {M("n\\times3=3n")}회 → {M("O(n)")}</div><p class="body-text">안쪽 반복은 n과 상관없이 <strong>항상 3번</strong>이다.<br>n이 커져도 늘어나는 것은 바깥 반복뿐이다.</p><p class="body-text key">O(n²)이라고 써도 틀린 상한은 아니지만, 증가율을 가장 정확히 보여 주는 O(n)으로 쓴다.</p>')}</div>
</div></div>''', cls='quiz', lesson=L)

def cards(spec):  # "4d 3 2 1" : d=done a=active p=pivot
    out = []
    for t in spec.split():
        cls = {'d':'done','a':'active','p':'pivot'}.get(t[-1], '') if not t[-1].isdigit() else ''
        num = t.rstrip('dap')
        out.append(f'<span class="{cls}">{num}</span>')
    return '<div class="number-cards">' + ''.join(out) + '</div>'

steps = [("처음", "4d 3 2 1", ""), ("3 넣기", "3a 4d 2 1", "비교 1번"), ("2 넣기", "2a 3d 4d 1", "비교 2번"), ("1 넣기", "1a 2d 3d 4d", "비교 3번")]
st = ''.join(f'<span class="step-name">{a}</span>{cards(b)}<span class="step-cmp">{c}</span>' for a,b,c in steps)
st += '<span class="step-name">합계</span><span class="step-sum">1 + 2 + 3 = <b>6번</b> = 4 × 3 ÷ 2</span>'
CASES_DEF = '<p class="cases-def">입력에 따라 일의 양이 다르다. <b>최선</b> 가장 적게 일하게 되는 입력 · <b>평균</b> 입력이 무작위 순서일 때의 평균 실행 횟수 · <b>최악</b> 가장 많이 일하게 되는 입력</p>'
INS = [("def insertion_sort(a):","세지 않음","m"),("    for i in range(1, len(a)):","n−1회"),("        j = i","n−1회"),
       ("        while j > 0 and a[j-1] > a[j]:","최악 n(n−1)/2회 · 최선 n−1회","f"),("            a[j-1], a[j] = a[j], a[j-1]","최악 n(n−1)/2회 · 최선 0회"),("            j -= 1","최악 n(n−1)/2회 · 최선 0회")]
slide('삽입 정렬: 하나씩 꺼내 <em>알맞은 자리에 끼워 넣기</em>', f'''<div class="lesson-content reveal">{CASES_DEF}<div class="split">
<div><p class="body-text sort-lead">새 원소를 왼쪽 원소와 하나씩 비교하며 앞으로 옮기다가,<br><strong>자기보다 작거나 같은 값을 만나거나 맨 앞에 닿으면 멈춘다.</strong></p>
 <div class="sort-steps">{st}</div>
 <div class="sort-legend"><span><i class="done"></i>정렬된 부분</span><span><i class="active"></i>방금 넣은 원소</span><span><i></i>아직 남은 원소</span></div></div>
<div class="case-list">
 <div class="case"><div><h3>최선 · 이미 정렬된 입력</h3><p>넣을 때마다 한 번 비교하고 바로 멈춤 → {M("n-1")}번</p></div><p class="formula">{M("O(n)")}</p></div>
 <div class="case"><div><h3>평균 · 무작위 순서의 입력</h3><p>넣을 때마다 앞 원소의 절반쯤과 비교 → 약 {M("\\dfrac{n^2}{4}")}번</p></div><p class="formula coral-text">{M("O(n^2)")}</p></div>
 <div class="case"><div><h3>최악 · 거꾸로 정렬된 입력</h3><p>넣을 때마다 앞 원소와 모두 비교 → {M("\\dfrac{n(n-1)}{2}")}번</p></div><p class="formula coral-text">{M("O(n^2)")}</p></div>
</div></div>
<details class="optional"><summary>코드로 보기 · 비교 횟수 주석</summary>{code(INS, cls="xs", label="정렬의 성능은 4번 줄의 원소 비교 횟수로 따진다", legend="# = 실행 횟수 (4번 줄은 비교 횟수)")}</details>
<p class="caption key">교과서 코드는 자리를 찾아도 멈추지 않아 항상 n(n−1)/2번 비교한다(최선도 O(n²)). 코드에 따라 최선이 달라진다.</p></div>''', lesson=L)

slide('퀵 정렬: 기준값으로 나누고, <em>나눈 쪽을 다시 정렬</em>', f'''<div class="lesson-content reveal"><div class="split">
<div class="partition">
 <div class="row"><span>처음</span>{cards("3 8 5p 1 7")}</div>
 <div class="row"><span>나누기</span><div class="partition-branches"><div>{cards("3 1")}<p>5보다 작은 쪽</p></div><div>{cards("5p")}<p>피벗(기준값)</p></div><div>{cards("8 7")}<p>5보다 큰 쪽</p></div></div></div>
 <p class="body-text">나뉜 두 쪽에도 같은 방법을 반복한다.</p>
 <details class="optional"><summary>더 알아보기 · 왜 n log n일까?</summary><p class="body-text">반씩 나뉘면 8 → 4 → 2 → 1로 3단계(3 = log₂8).<br>단계마다 원소 n개를 한 번씩 비교하므로 약 n × log₂n번이다.</p></details></div>
<div class="case-list">
 <div class="case"><div><h3>최선</h3><p>매번 반씩 균형 있게 나뉠 때</p></div><p class="formula fc-nlog">{M("O(n\\log n)")}</p></div>
 <div class="case"><div><h3>평균</h3><p>입력이 무작위 순서일 때 평균적으로</p></div><p class="formula fc-nlog">{M("O(n\\log n)")}</p></div>
 <div class="case"><div><h3>최악</h3><p>매번 한쪽으로만 치우칠 때<br>(예: 첫 원소를 피벗으로 고르는데 입력이 이미 정렬된 경우)</p></div><p class="formula coral-text">{M("O(n^2)")}</p></div>
</div></div>
<p class="caption">같은 n이라도 입력 순서와 피벗을 고르는 방법에 따라 나뉘는 모양이 달라진다.</p></div>''', lesson=L)

slide('퀵 정렬은 <em>항상</em> 더 빠를까?', f'''<div class="lesson-content reveal"><div class="split">
<div><p class="quote">“퀵 정렬은 O(n log n),<br>삽입 정렬은 O(n²)이니까<br>언제나 퀵 정렬이 빠르다.”</p>
 <table class="lesson-table case-table"><thead><tr><th></th><th>최선</th><th>평균</th><th>최악</th></tr></thead><tbody>
 <tr><td>삽입 정렬</td><td>{M("O(n)")}</td><td>{M("O(n^2)")}</td><td>{M("O(n^2)")}</td></tr>
 <tr><td>퀵 정렬</td><td>{M("O(n\\log n)")}</td><td>{M("O(n\\log n)")}</td><td>{M("O(n^2)")}</td></tr></tbody></table></div>
<div><span class="quiz-tag">Q6</span>
 <p class="question">이 주장의 어디가 틀렸을까?<br>왼쪽 표를 보며 <strong>두 가지</strong>를 찾아보자.</p>
 {answer("q6", '<div class="answer-equation">항상 그렇지는 않다.</div><p class="body-text">① 경우를 맞추지 않았다. 퀵 정렬의 <strong>평균</strong>과 삽입 정렬의 <strong>최악</strong>을 견줬다. 이미 정렬된 입력이면 삽입 정렬은 O(n)이지만, 첫 원소를 피벗으로 고르는 퀵 정렬은 피벗이 늘 가장 작은 값이라 O(n²)이다.</p><p class="body-text">② 빅오는 계수와 상수를 생략한다. n이 작을 때는 실제 실행 횟수가 뒤집힐 수 있다.</p><p class="body-text key">빅오는 최선·평균·최악 어느 경우에도 쓸 수 있다. O 자체가 ‘최악’이라는 뜻은 아니다.</p>')}</div>
</div></div>''', cls='quiz', lesson=L)

slide('2차시 정리:<br><em>이제 근거를 들어 비교할 수 있다.</em>', f'''<div class="lesson-content reveal"><div class="three-points">
<article><b>01</b><h3>코드 → 횟수</h3><p class="body-text">반복 범위를 읽고<br>줄마다 실행 횟수를 적는다.</p></article>
<article><b>02</b><h3>횟수 → 빅오</h3><p class="body-text">최고차항만 남기고 계수를 떼어<br>증가율의 상한으로 나타낸다.</p></article>
<article><b>03</b><h3>비교 → 선택</h3><p class="body-text">최선·평균·최악과 입력 크기를<br>함께 따져 알고리즘을 고른다.</p></article>
</div><p class="hand note">마지막으로, 출구 질문!</p></div>''', cls='bigo', lesson=L)

slide('2차시 마무리: <em>출구 질문</em>', f'''<div class="lesson-content reveal"><div class="split">
<div><div class="case-list">
 <div class="case"><div><h3>알고리즘 P</h3><p>실행 횟수</p></div><p class="formula fc-n2">{M("n^2")}</p></div>
 <div class="case"><div><h3>알고리즘 Q</h3><p>실행 횟수</p></div><p class="formula fc-nlog">{M("50\\,n\\log_2 n")}</p></div></div>
 <table class="lesson-table"><thead><tr><th>n</th><th class="num">P</th><th class="num">Q</th></tr></thead><tbody>
 <tr><td>10</td><td class="num">{AQ("?","100")}</td><td class="num">{AQ("?","약 1,650")}</td></tr>
 <tr><td>1,000</td><td class="num">{AQ("?","1,000,000")}</td><td class="num">{AQ("?","약 500,000")}</td></tr></tbody></table>
 <p class="hint">힌트: log₂10 ≈ 3.3, &nbsp;log₂1,000 ≈ 10</p></div>
<div><span class="quiz-tag">출구 질문</span>
 <ol class="question"><li>n = 10일 때 일을 덜 하는 쪽은?</li><li>n = 1,000일 때는?</li><li>두 결과를 빅오로 설명해 보자.</li></ol>
 {answer("exit2", '<div class="answer-equation">n = 10 → P &nbsp;/&nbsp; n = 1,000 → Q</div><p class="body-text">P는 O(n²), Q는 O(n log n)이다. n이 크면 Q가 훨씬 유리하지만, 계수 50 때문에 n이 작을 때는 P가 일을 덜 한다. 빅오는 ‘n이 충분히 클 때’의 비교다(Q6의 ②).</p><p class="small">어림값이면 충분하다(정확히는 약 1,661, 약 498,289). 다음 시간(선택 실습): 같은 답을, 더 적은 검사로!</p>')}</div>
</div></div>''', cls='quiz', lesson=L)

# =========================================================
# 3차시
# =========================================================
L = 3
def tri(a, b, c, label_pos):
    pass
U = 46.25
def tri_svg(a, b, c):
    # 밑변 c를 가운데 놓고, 세 변 a(왼쪽), b(오른쪽)인 삼각형. 모두 같은 축척.
    base = c * U; x0 = 125 - base / 2; x1 = x0 + base
    xa = (a*a*U*U - b*b*U*U + base*base) / (2*base)
    h = math.sqrt(max(a*a*U*U - xa*xa, 0))
    px, py = x0 + xa, 135 - h
    cx, cy = (x0 + x1 + px) / 3, (270 + py) / 3
    def out(ax, ay, bx, by):
        mx, my = (ax + bx) / 2, (ay + by) / 2
        nx, ny = -(by - ay), (bx - ax); L = math.hypot(nx, ny); nx, ny = nx / L, ny / L
        if (mx - cx) * nx + (my - cy) * ny < 0: nx, ny = -nx, -ny
        return mx + nx * 16 - 7, my + ny * 16 + 8
    lx, ly = out(x0, 135, px, py)
    rx, ry = out(x1, 135, px, py)
    return (f'<svg viewBox="0 0 250 170" role="img" aria-label="변의 길이가 {a}, {b}, {c}인 삼각형">'
            f'<path d="M{x0:.2f} 135 L{px:.2f} {py:.2f} L{x1:.2f} 135 Z" fill="#dfefe6" stroke="#007f73" stroke-width="4"/>'
            f'<text x="{lx:.1f}" y="{ly:.1f}">{a}</text><text x="{rx:.1f}" y="{ry:.1f}">{b}</text><text x="{125-7}" y="163">{c}</text></svg>')
tris = ''.join(f'<article>{tri_svg(a,b,c)}<p>({x}, {y}, {z})</p></article>' for (a,b,c),(x,y,z) in [((1,4,4),(1,4,4)),((2,3,4),(2,3,4)),((3,3,3),(3,3,3))])
slide('둘레가 9인 삼각형,<br><em>몇 가지 만들 수 있을까?</em>', f'''<div class="lesson-content reveal">
<p class="goal"><b>3차시 목표</b>같은 답을 더 적은 검사로 구하도록 반복을 줄이고, 그 효과를 빅오로 설명할 수 있다.</p>
<p class="body-text">세 변의 길이는 자연수, 둘레는 9. (2, 3, 4)와 (3, 2, 4)처럼 <strong>순서만 다른 것은 같은 삼각형</strong>으로 센다.</p>
<div class="tri-try"><span class="ok">✔ (2, 3, 4): 삼각형이 된다</span><span class="no">✘ (1, 1, 7): 7 ≥ 1 + 1이라 안 된다</span></div>
<p class="hand note hide-on-reveal">빠짐없이, 중복 없이 세려면 어떻게 할까?</p>
{answer("tri-all", f'<div class="triangle-examples">{tris}</div><p class="body-text">모두 3가지. 다음 장부터 컴퓨터로 빠짐없이 세어 확인해 보자.</p>', label="가능한 삼각형 모두 보기")}
</div>''', cls='cover', lesson=L)

slide('후보가 <em>삼각형이 되려면?</em>', f'''<div class="lesson-content reveal"><div class="three-points">
<article><b>01</b><h3>순서 정하기</h3><p class="formula">{M("1\\le a\\le b\\le c")}</p><p class="body-text">작은 변부터 차례로 정하면<br>순서만 다른 중복이 생기지 않는다.</p></article>
<article><b>02</b><h3>둘레 확인</h3><p class="formula">{M("a+b+c=n")}</p><p class="body-text">세 변을 더하면<br>주어진 둘레 n과 같다.</p></article>
<article><b>03</b><h3>삼각형 확인</h3><p class="formula">{M("c<a+b")}</p><p class="body-text">가장 긴 변 c가 나머지 두 변의 합보다 짧다.<br>c가 가장 기니 이것 하나만 확인하면 된다.</p></article>
</div><p class="hand note">(1, 2, 6): 합은 9지만 6 ≥ 1 + 2 → 삼각형이 아니다.</p></div>''', lesson=L)

TRIPLE = [("n = 9","1회"),("ans = 0","1회"),("checks = 0","1회"),("for a in range(1, n + 1):","9회"),("    for b in range(a, n + 1):","45회"),
          ("        for c in range(b, n + 1):","165회"),("            checks += 1","165회","f"),("            if a + b + c == n and c < a + b:","165회"),
          ("                ans += 1","3회"),("print(ans, checks)","1회")]
slide('세 변을 <em>하나씩 모두 확인한다.</em>', f'''<div class="lesson-content reveal"><div class="split code-left">
<div>{code(TRIPLE, id="triple-code", cls="xs", label="n = 9일 때의 실행 횟수")}
 <div class="copy-row"><button type="button" class="copy-code" data-copy="triple-code">코드 복사</button><span class="copy-status" role="status"></span></div></div>
<div><p class="body-text"><strong>ans</strong>: 조건을 만족한 삼각형의 수<br><strong>checks</strong>: if로 후보를 검사한 횟수</p>
 <div class="output">실행 결과 <b>3 165</b></div>
 <p class="body-text">삼각형은 3개뿐인데,<br>후보는 <strong>165개</strong>나 검사했다.<br>대부분은 합이 9도 아닌 후보다.</p>
 <p><a class="colab" href="https://colab.research.google.com/notebooks/empty.ipynb" target="_blank" rel="noopener noreferrer">빈 Colab 노트북 열기 ↗</a></p></div>
</div></div>''', cls='lab-slide', lesson=L)

slide('실행해 보고, <em>n만 바꿔 보자.</em>', f'''<div class="lesson-content reveal">
<div class="lab-steps"><span>① <a href="https://colab.research.google.com/notebooks/empty.ipynb" target="_blank" rel="noopener noreferrer">빈 Colab 열기 ↗</a></span><span>② 26장 ‘코드 복사’로 붙여넣기</span><span>③ Shift + Enter로 실행</span><span>④ 1번 줄 n을 9, 10, 30으로</span></div>
<table class="lesson-table lab-table"><thead><tr><th>입력 n</th><th class="num">삼각형 수 ans</th><th class="num">검사 횟수 checks</th></tr></thead>
<tbody><tr><td>9</td><td class="num">3</td><td class="num">165</td></tr></tbody>
<tbody id="lab-results" hidden><tr><td>10</td><td class="num">2</td><td class="num">220</td></tr><tr><td>30</td><td class="num">19</td><td class="num">4,960</td></tr></tbody></table>
<ol class="question think"><li>n이 9 → 30으로 약 3.3배가 될 때, checks는 약 몇 배가 될까? {AQ("","→ 약 30배. 반복이 세 겹이라 n³처럼 늘어난다. 더 큰 n에서 같은 비교를 하면 (30/9)³ ≈ 37배에 가까워진다.")}</li>
<li>둘레가 9 → 10으로 늘었는데 삼각형은 3 → 2로 줄었다. 왜일까? {AQ("","→ a = 1이면 c &lt; 1 + b, c ≥ b를 함께 만족하려면 b = c여야 한다. 둘레 9는 (1, 4, 4)가 되지만, 둘레 10은 b + c = 9를 똑같이 나눌 수 없다. 정답 수는 n이 커져도 항상 늘지는 않지만, 검사 횟수는 항상 는다.")}</li></ol>
<p>{'<button class="answer-toggle" type="button" aria-expanded="false" aria-controls="lab-results">n = 10, 30 결과 확인</button>'}</p>
<p class="caption">먼저 결과를 예상해 적은 뒤 실행해 비교하자. Colab은 Google 로그인이 필요할 수 있으며, 접속이 어려우면 이 표로 같은 활동을 진행한다.</p></div>''', lesson=L)

slide('세 번째 변은 <em>계산하면 된다.</em>', f'''<div class="lesson-content reveal">
<div class="hero-math">{M("c=n-a-b")}</div>
<div class="split"><p class="body-text">a + b + c = n이므로<br>a와 b를 정하면 c는 <strong>하나로 정해진다.</strong></p>
<p class="body-text">c를 1부터 n까지 하나씩 바꿔 볼 필요가 없다.<br>계산한 c가 조건을 만족하는지만 확인하면<br>가능한 삼각형을 빠뜨리지 않는다.</p></div>
<div class="callout">확인할 조건 두 가지 · {M("c\\ge b")}: 순서 유지(그러면 c ≥ 1도 자동으로 성립) · {M("c<a+b")}: 삼각형</div>
<p class="hand note">반복을 지우기 전에, 같은 답이 나오는지 확인!</p></div>''', lesson=L)

DOUBLE = [("n = 9","1회"),("ans = 0","1회"),("checks = 0","1회"),("for a in range(1, n + 1):","9회"),("    for b in range(a, n + 1):","45회"),
          ("        c = n - a - b","45회"),("        checks += 1","45회","f"),("        if c >= b and c < a + b:","45회"),("            ans += 1","3회"),("print(ans, checks)","1회")]
slide('반복 두 개로 <em>같은 답을 구한다.</em>', f'''<div class="lesson-content reveal"><div class="split code-left">
<div>{code(DOUBLE, id="double-code", cls="xs", label="n = 9일 때의 실행 횟수")}
 <div class="copy-row"><button type="button" class="copy-code" data-copy="double-code">코드 복사</button><span class="copy-status" role="status"></span></div></div>
<div><p class="body-text">a, b만 반복하고 c는 계산한다.<br>1번 줄 n을 9, 10, 30으로 바꿔 보자.</p>
 <div class="output">실행 결과 <b>3 45</b></div>
 <p class="body-text">삼각형 수는 <strong>3으로 같고</strong>,<br>검사 횟수는 165 → <strong>45</strong>로 줄었다.</p>
 <p><a class="colab" href="https://colab.research.google.com/notebooks/empty.ipynb" target="_blank" rel="noopener noreferrer">빈 Colab 노트북 열기 ↗</a></p></div>
</div>
<details class="optional"><summary>먼저 끝났다면 · 조건 설명하기</summary><p class="body-text">왜 c ≥ b를 확인할까? 8번 줄에서 <code>c &gt;= b and</code>를 지우고 n = 9로 실행해 보자. 몇 개가 세어지고, 어떤 후보가 섞일까?</p>
{answer("cb-ans", '<p class="body-text">41개가 세어진다. c가 0 이하인 후보 29개(예: (1, 8, 0))와, c가 b보다 작아 순서가 깨진 후보 9개가 섞인다. 그중 (2, 4, 3)처럼 이미 센 삼각형의 중복도 있고, (1, 5, 3)처럼 실제로는 삼각형이 아닌 것((1, 3, 5): 5 ≥ 1 + 3)도 있다.</p><p class="body-text">c가 가장 긴 변이 아니면 c &lt; a + b 하나만으로는 삼각형인지 판정할 수 없다.</p>', label="교사용 정답 보기")}</details>
</div>''', cls='lab-slide', lesson=L)

slide('결과는 같게, <em>검사는 더 적게.</em>', f'''<div class="lesson-content reveal">
<table class="lesson-table"><thead><tr><th>n</th><th class="num">삼중 반복 검사</th><th class="num">이중 반복 검사</th><th class="num">몇 배 줄었나</th><th class="num">두 코드의 정답</th></tr></thead><tbody>
<tr><td>9</td><td class="num">165</td><td class="num">45</td><td class="num">약 3.7배</td><td class="num">3</td></tr>
<tr><td>10</td><td class="num">220</td><td class="num">55</td><td class="num">4배</td><td class="num">2</td></tr>
<tr><td>30</td><td class="num">4,960</td><td class="num">465</td><td class="num hl">약 10.7배</td><td class="num">19</td></tr></tbody></table>
<div class="split"><div><span class="quiz-tag">Q7</span>
 <ol class="question"><li>두 코드의 검사 횟수를 빅오로 나타내면?</li><li>반복 하나를 없앨 수 있었던 근거는?</li><li>n이 커질수록 ‘몇 배’는 어떻게 변할까?</li></ol>
 <p class="caption">checks는 if로 후보를 검사한 횟수다. 1차시의 ‘모든 줄의 실행 횟수 T(n)’과는 다른 기준이다.</p></div>
<div>{answer("q7", f'<div class="answer-equation">① {M("O(n^3)")} → {M("O(n^2)")}</div><p class="body-text">② 합 조건 a + b + c = n 덕분에 a, b를 정하면 c가 정해져, c를 바꾸는 반복을 계산 한 줄로 바꿨다.</p><p class="body-text">③ 약 {M("\\dfrac{n+2}{3}")}배로, n에 비례해 계속 커진다. 차수가 하나 낮아졌기 때문이다.</p>')}</div></div></div>''', cls='quiz', lesson=L)

slide('좋은 알고리즘은<br><em>근거를 들어 설명할 수 있다.</em>', f'''<div class="lesson-content reveal"><div class="three-points">
<article><b>01</b><h3>정확한가?</h3><p class="body-text">빠짐없이, 중복 없이<br>정답을 구하는가?</p></article>
<article><b>02</b><h3>얼마나 일하는가?</h3><p class="body-text">무엇을 1회로 셀지<br>기준을 분명히 정했는가?</p></article>
<article><b>03</b><h3>어떻게 커지는가?</h3><p class="body-text">입력 크기에 따른 증가율을<br>빅오로 설명할 수 있는가?</p></article>
</div><p class="hand note">코드를 줄이는 것보다, 불필요한 일을 줄이는 것.</p></div>''', cls='bigo', lesson=L)

total = len(slides)
body = '\n'.join(s.replace('TOTAL', str(total)) for s in slides)
page = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>같은 답, 다른 속도 — 알고리즘의 성능과 분석</title>
<meta name="description" content="고등학교 정보과학 · 알고리즘의 성능과 분석 · 수업용 HTML 슬라이드 {total}장 · 2차시와 선택 실습">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%233156d3'/%3E%3Ctext x='7' y='24' font-size='25' fill='white'%3En%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="assets/katex/katex.min.css"><link rel="stylesheet" href="styles.css">
<script defer src="assets/katex/katex.min.js"></script><script defer src="slides.js"></script>
<noscript><style>#lab-results[hidden]{{display:table-row-group!important}}.answer-slot [hidden]{{display:block!important}}.code .cnt-a,.ans-a{{display:inline}}.code .cnt-q,.ans-q{{display:none}}.answer-toggle,.play,.copy-row,.graph-values .small{{display:none!important}}#rev2,#tbl-ans,.question.think .ans-a{{display:inline!important}}</style></noscript>
</head>
<body>
<header class="reader"><span>정보과학 <b>/</b> 알고리즘의 성능과 분석</span><span class="keys"><kbd>→</kbd> <kbd>←</kbd> 한 장씩 넘기기</span><span id="progress-text">진행 0%</span><div class="track" role="progressbar" aria-label="자료 진행" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><div id="progress"></div></div></header>
<main>
{body}
</main>
</body>
</html>
'''
open(OUT, 'w', encoding='utf-8').write(page)
print('slides:', total)
