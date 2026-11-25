import Nc.Hc.Vnp

open Nc

-- Independent packaging of the witness in the released internal class definition.
-- The witness identities and size calculus are imported from the fresh build.
example (F : Type*) [Field F] :
    ({ X := fun n => Fin n × Fin n, poly := genHC F } : Family F) ∈ VNP F := by
  refine ⟨fun n => n * n, Hc.hcWit F, ⟨700, fun n => ?_⟩, Hc.genHC_eq_sum_wit F⟩
  have hb := Hc.quartic_bound n (C := 700) le_rfl
  obtain ⟨hs, hd⟩ := Hc.csize_hcWit F n
  refine ⟨le_trans ?_ hb, hd.trans hb, hs.mono hb⟩
  simp only [Fintype.card_sum, Fintype.card_prod, Fintype.card_fin]
  nlinarith [Nat.zero_le (n ^ 4), Nat.zero_le (n ^ 3), Nat.zero_le (n ^ 2)]

#check @Hc.sum_cycles_eq_sum_orders
#check @Hc.exists_order_of_test_ne_zero
#check @Hc.genHC_eq_sum_wit
#check @Hc.csize_hcWit
#check @Hc.quartic_bound
#print axioms Nc.Hc.sum_cycles_eq_sum_orders
#print axioms Nc.Hc.exists_order_of_test_ne_zero
#print axioms Nc.Hc.genHC_eq_sum_wit
#print axioms Nc.Hc.csize_hcWit
#print axioms Nc.Hc.quartic_bound
