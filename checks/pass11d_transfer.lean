import Paper.Transfer

#check @Nc.exists_common_ring
#print axioms Nc.exists_common_ring
#check @Nc.exists_specialisation
#print axioms Nc.exists_specialisation
#check @Paper.lem_transfer
#print axioms Paper.lem_transfer

/-- A constant satisfying this equation cannot be specialized into the prime field of order two. -/
theorem prime_field_obstruction (a : ZMod 2) : a ^ 2 + a + 1 ≠ 0 := by
  fin_cases a <;> decide

#print axioms prime_field_obstruction
