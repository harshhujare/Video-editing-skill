#!/usr/bin/env python3
"""Unit tests for prep_and_align_explainer.py."""

import unittest

from prep_and_align_explainer import (
    map_display_script_to_asr,
    parse_display_script,
    sculpt_silence_intervals,
    slice_explainer_beats,
)


class ExplainerAlignerTests(unittest.TestCase):
    def test_sculpt_silence_preserves_short_pauses_and_compresses_long_gaps(self) -> None:
        # Total 5.0s: leading silence 0..0.3, short internal pause 1.2..1.6 (400ms <= 650ms),
        # long internal pause 2.5..3.9 (1400ms > 650ms), trailing silence 4.7..5.0.
        silences = [(0.0, 0.3), (1.2, 1.6), (2.5, 3.9), (4.7, 5.0)]
        intervals = sculpt_silence_intervals(
            5.0, silences, edge_pad_s=0.03, max_gap_s=0.65, target_gap_s=0.32
        )
        # Expect two intervals: (0.27, 2.66) and (3.74, 4.73) -> long gap compressed to 0.32s total
        self.assertEqual(len(intervals), 2)
        self.assertAlmostEqual(intervals[0][0], 0.27, places=3)
        self.assertAlmostEqual(intervals[0][1], 2.66, places=3)
        self.assertAlmostEqual(intervals[1][0], 3.74, places=3)
        self.assertAlmostEqual(intervals[1][1], 4.73, places=3)

    def test_dual_script_mapper_snaps_phonetic_marathi_to_clean_display_tokens(self) -> None:
        script = "दरमहा ₹50,000 गुंतवा\n[SCENE]\nआणि SIP सुरू ठेवा?"
        groups, flat = parse_display_script(script)
        self.assertEqual(len(groups), 2)
        self.assertEqual(flat, ["दरमहा", "₹50,000", "गुंतवा", "आणि", "SIP", "सुरू", "ठेवा?"])

        asr_words = [
            {"word": "दरमहा", "start_ms": 0, "end_ms": 420},
            {"word": "पन्नास", "start_ms": 430, "end_ms": 780},
            {"word": "हजार", "start_ms": 790, "end_ms": 1120},
            {"word": "रुपये", "start_ms": 1130, "end_ms": 1480},
            {"word": "गुंतवा", "start_ms": 1500, "end_ms": 2050},
            {"word": "आणि", "start_ms": 2350, "end_ms": 2650},
            {"word": "एस", "start_ms": 2670, "end_ms": 2880},
            {"word": "आय", "start_ms": 2890, "end_ms": 3090},
            {"word": "पी", "start_ms": 3100, "end_ms": 3350},
            {"word": "सुरू", "start_ms": 3380, "end_ms": 3790},
            {"word": "ठेवा", "start_ms": 3800, "end_ms": 4250},
        ]
        aligned = map_display_script_to_asr(flat, asr_words, fps=60)
        self.assertEqual([w["word"] for w in aligned], flat)
        # ₹50,000 must inherit start of 'पन्नास' (430) and end of 'रुपये' (1480)
        self.assertEqual(aligned[1]["start_ms"], 430)
        self.assertEqual(aligned[1]["end_ms"], 1480)
        # SIP must inherit start of 'एस' (2670) and end of 'पी' (3350)
        self.assertEqual(aligned[4]["start_ms"], 2670)
        self.assertEqual(aligned[4]["end_ms"], 3350)

        timeline = slice_explainer_beats(aligned, groups, fps=60)
        scenes = timeline["scenes"]
        self.assertGreaterEqual(len(scenes), 2)
        for i in range(len(scenes) - 1):
            self.assertEqual(
                scenes[i]["exit_transition"]["type"],
                scenes[i + 1]["enter_transition"]["type"],
            )


if __name__ == "__main__":
    unittest.main()
