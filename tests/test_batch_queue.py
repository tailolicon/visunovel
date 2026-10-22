"""Batch allocation invariants for the private visuNovel worker fleet."""
import unittest
from scripts.batch_queue import owner,batch,get_plan,check_plan

class TestBatchAllocation(unittest.TestCase):
    def setUp(self):self.plan=get_plan()

    def test_first_five_lanes(self):
        assert [batch(i,0,self.plan)["chapters"] for i in range(1,6)] == [
          [137,138,139,140,141],[142,143,144,145,146],
          [147,148,149,150,151],[152,153,154,155,156],[157,158,159,160,161]]
    
    def test_no_overlap_two_waves(self):
        assignments=[batch(l,w,self.plan) for w in range(2) for l in range(1,6)]
        chapters=[c for item in assignments for c in item["chapters"]]
        self.assertEqual(chapters,list(range(137,187)))
        self.assertEqual(len(set(chapters)),len(chapters))
        for item in assignments:
            for c in item["chapters"]:
                self.assertEqual(owner(c,self.plan),item["lane"])
    def test_branch_ownership_remains_stable(self):
        for lane in range(1,6):
            a,b=batch(lane,0,self.plan),batch(lane,1,self.plan)
            self.assertEqual(a["branch"],b["branch"])
            self.assertEqual(b["first"]-a["first"],25)
    
    def test_reject_early_chapter(self):
        with self.assertRaises(ValueError):owner(136,self.plan)

    def test_bad_slots_rejected(self):
        p=dict(self.plan,hourly_minute_offsets=[0,12,24,24,48])
        with self.assertRaises(ValueError):check_plan(p)

    def test_bad_lane_rejected(self):
        with self.assertRaises(ValueError):batch(0,0,self.plan)
        with self.assertRaises(ValueError):batch(6,0,self.plan)

if __name__=="__main__": unittest.main()
