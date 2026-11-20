"""Build all ten experiment write-ups into research_experiments/docs/."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import content_a  # noqa: E402

FIG = HERE / "figures"
OUT = HERE / "docs"
OUT.mkdir(exist_ok=True)

NAMES = {
    1: "Experiment_1_Research_Problem_and_Gap_Analysis_CourtVisionAI.docx",
    2: "Experiment_2_Research_Planning_and_Methodology_Design_CourtVisionAI.docx",
    3: "Experiment_3_Dataset_Experimental_Setup_Preparation_CourtVisionAI.docx",
    4: "Experiment_4_Implementation_and_Experimental_Validation_CourtVisionAI.docx",
    5: "Experiment_5_Data_Analysis_and_Visualization_CourtVisionAI.docx",
    6: "Experiment_6_Technical_Paper_Preparation_CourtVisionAI.docx",
    7: "Experiment_7_Plagiarism_Peer_Review_and_Revision_CourtVisionAI.docx",
    8: "Experiment_8_Patent_Copyright_Trademark_Prior_Art_Search_CourtVisionAI.docx",
    9: "Experiment_9_IPR_Document_Preparation_CourtVisionAI.docx",
    10: "Experiment_10_Research_Dissemination_and_Innovation_Showcase_CourtVisionAI.docx",
}


def main(only=None):
    build = {
        1: lambda p: content_a.exp1(p),
        2: lambda p: content_a.exp2(p, FIG),
        3: lambda p: content_a.exp3(p),
        8: lambda p: content_a.exp8(p),
        9: lambda p: content_a.exp9(p, FIG),
    }
    summary = HERE / "eval" / "results" / "summary.json"
    if summary.exists():
        import content_b
        R = json.loads(summary.read_text())
        build.update({
            4: lambda p: content_b.exp4(p, FIG, R),
            5: lambda p: content_b.exp5(p, FIG, R),
            6: lambda p: content_b.exp6(p, FIG, R),
            7: lambda p: content_b.exp7(p, FIG, R),
            10: lambda p: content_b.exp10(p, FIG, R),
        })
    for n in sorted(build):
        if only and n not in only:
            continue
        path = OUT / NAMES[n]
        build[n](path)
        print("built", path.name)


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or None)
