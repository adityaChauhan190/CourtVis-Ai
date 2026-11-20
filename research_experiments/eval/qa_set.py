"""
Ground-truth question set for the Court Vision AI grounding experiment.

Source document: Jacob Mathew v. State of Punjab & Anr., (2005) 6 SCC 1
(the 20-page judgment stored in backend/storage/documents).

Each question has:
  id        - A* = answer lies inside the first 18,000 characters (what the
                   production pipeline actually sends to the LLM)
              B* = answer lies in the document but AFTER the 18,000-char cut
              C* = NOT answerable from the document (should be refused)
  q         - question text
  gold      - list of regexes; ALL must match (case-insensitive) for the answer
              to be scored correct.  Empty for C* questions.
  page      - page of the judgment where the answer appears (A/B only)
"""

QA = [
    # ── A: inside the production context window ─────────────────────────────
    dict(id="A01", page=1, q="On what date was Jiwan Lal Sharma admitted to the hospital?",
         gold=[r"15(th)?[\s./-]*(0?2|feb)", r"1995"]),
    dict(id="A02", page=1, q="In which hospital and city was the patient admitted?",
         gold=[r"cmc|christian medical", r"ludhiana"]),
    dict(id="A03", page=1, q="Under which sections of the Indian Penal Code was the offence registered on the FIR?",
         gold=[r"304\s*-?\s*a", r"\b34\b"]),
    dict(id="A04", page=1, q="For how long did no doctor turn up after the duty nurse was contacted?",
         gold=[r"20\s*(to|-|–|or)\s*25"]),
    dict(id="A05", page=1, q="Which two doctors came to the patient's room?",
         gold=[r"jacob mathew", r"allen joseph"]),
    dict(id="A06", page=1, q="What was found to be wrong with the oxygen cylinder connected to the patient?",
         gold=[r"empty"]),
    dict(id="A07", page=1, q="How many minutes were wasted while trying to make the second gas cylinder functional?",
         gold=[r"5\s*(to|-|–|or)\s*7"]),
    dict(id="A08", page=2, q="On what date did the High Court dismiss the petition filed under Section 482 CrPC?",
         gold=[r"18(th)?[\s./-]*(12|dec)", r"2002"]),
    dict(id="A09", page=2, q="On what date was the application for recalling the High Court's order dismissed?",
         gold=[r"24(th)?[\s./-]*(0?1|jan)", r"2003"]),
    dict(id="A10", page=2, q="The referring two-judge Bench doubted the correctness of which earlier decision?",
         gold=[r"suresh gupta"]),
    dict(id="A11", page=2, q="On what date did the two-judge Bench refer the matter to a three-judge Bench?",
         gold=[r"\b9(th)?[\s./-]*(0?9|sep)", r"2004"]),
    dict(id="A12", page=2, q="According to the appellant, what disease was the deceased suffering from?",
         gold=[r"cancer"]),
    dict(id="A13", page=3, q="Which body did the Supreme Court issue notice to so that it could assist the Court at the hearing?",
         gold=[r"medical council of india"]),
    dict(id="A14", page=5, q="In Andrews v. Director of Public Prosecutions, which Law Lord said that simple lack of care such as will constitute civil liability is not enough?",
         gold=[r"atkin"]),
    dict(id="A15", page=4, q="What are the three essential components of negligence described in the judgment?",
         gold=[r"duty", r"breach", r"damage"]),
    dict(id="A16", page=5, q="In which Supreme Court decision was the statement of law in Andrews approved?",
         gold=[r"sy[ae]d (akbar|kabar)"]),

    # ── B: in the document, but beyond the 18,000-character cut ─────────────
    dict(id="B01", page=6, q="Which English case laid down the test for medical negligence that the Court held applicable in India? Give the full case name.",
         gold=[r"bolam", r"friern"]),
    dict(id="B02", page=19, q="According to the guidelines, what must a private complainant produce before a criminal complaint against a doctor is entertained?",
         gold=[r"opinion", r"(competent|another) doctor"]),
    dict(id="B03", page=19, q="From whom should the investigating officer preferably obtain a medical opinion before proceeding against an accused doctor?",
         gold=[r"government service"]),
    dict(id="B04", page=17, q="According to the conclusions, how must the expression 'rash or negligent act' in Section 304A IPC be read?",
         gold=[r"gross"]),
    dict(id="B05", page=14, q="In Juggankhan v. State of Madhya Pradesh, what substances did the homoeopath administer to the patient?",
         gold=[r"stramonium|dhatura"]),
    dict(id="B06", page=15, q="In Achutrao Haribhau Khodwa v. State of Maharashtra, what was left inside the patient's abdomen?",
         gold=[r"\bmop\b"]),
    dict(id="B07", page=13, q="Which Privy Council case involved a doctor who administered an overdose of a Sobita injection?",
         gold=[r"akerele"]),
    dict(id="B08", page=20, q="What was the final result of the appeals?",
         gold=[r"allowed|quash"]),
    dict(id="B09", page=10, q="Which book by Alan Merry and Alexander McCall Smith does the Court rely on?",
         gold=[r"errors,?\s+medicine\s+and\s+the\s+law"]),
    dict(id="B10", page=10, q="Which section of the IPC in the chapter on General Exceptions exempts acts not intended to cause death, done by consent in good faith for the person's benefit?",
         gold=[r"\b88\b"]),
    dict(id="B11", page=19, q="Should a doctor accused of rashness or negligence be arrested in a routine manner, according to the guidelines?",
         gold=[r"routine|not be arrested|withheld|unless"]),
    dict(id="B12", page=8, q="In Maynard v. West Midlands Regional Health Authority, which Law Lord delivered the leading speech quoting Hunter v. Hanley?",
         gold=[r"scarman"]),
    dict(id="B13", page=8, q="Can a case under Section 304A IPC be decided solely by applying the rule of res ipsa loquitur?",
         gold=[r"(cannot|can ?not|not).{0,80}(solely|per se|alone|by itself|on its own)|rule of evidence|limited application"]),
    dict(id="B14", page=20, q="On the facts, what did the Court say was the probable cause of the problem, for which the hospital rather than the doctor may be liable?",
         gold=[r"oxygen|gas cylinder", r"hospital"]),

    # ── C: not answerable from the document (must be refused) ───────────────
    dict(id="C01", q="What was the name of the duty nurse who called the doctor?", gold=[]),
    dict(id="C02", q="What sentence of imprisonment did the trial court impose on Dr. Jacob Mathew?", gold=[]),
    dict(id="C03", q="How much compensation was awarded to Ashok Kumar Sharma?", gold=[]),
    dict(id="C04", q="What cause of death was recorded in the post-mortem report?", gold=[]),
    dict(id="C05", q="Which senior advocate argued the case for the appellant?", gold=[]),
    dict(id="C06", q="What was the name of the company that supplied the oxygen cylinders to the hospital?", gold=[]),
    dict(id="C07", q="What was the room number of the private ward in which the patient was admitted?", gold=[]),
    dict(id="C08", q="What was the age of Jiwan Lal Sharma at the time of his death?", gold=[]),
    dict(id="C09", q="What was the FIR number registered at Police Station Division No. 3, Ludhiana?", gold=[]),
    dict(id="C10", q="On what exact date was the FIR lodged by Ashok Kumar Sharma?", gold=[]),
    dict(id="C11", q="What disciplinary action did the Medical Council of India recommend against Dr. Jacob Mathew?", gold=[]),
    dict(id="C12", q="Which section of the Bharatiya Nyaya Sanhita, 2023 did the Court apply in this judgment?", gold=[]),
]

# Phrases that indicate the system declined to answer / said the info is absent.
ABSTAIN_PATTERNS = [
    r"not available in the (uploaded )?documents?",
    r"(is|are|was|were) not (available|mentioned|stated|specified|provided|contained|disclosed|found|given|recorded|identified|named)",
    r"does not (mention|state|specify|provide|contain|disclose|name|identify|record|indicate|refer)",
    r"do not (mention|state|specify|provide|contain|disclose|name|identify|record|indicate|refer)",
    r"no (information|mention|reference|record|details?) (is|are|of|about|regarding|on)",
    r"not (mentioned|stated|specified|disclosed|provided|named) in",
    r"cannot be (determined|answered|ascertained)",
    r"no such (section|information|sentence|award|order)",
    r"\bunknown\b",
    r"(did|does) not apply|predat|not (yet |been )?(in force|enacted|exist)",
    r"i (do not|don['’]t) (know|have)",
    r"(did|does) not (rely|apply|use|refer|invoke)",
    r"(long )?before the .{0,60}came into force",
]
