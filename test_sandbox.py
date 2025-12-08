from solver.solver import solve_mathler_with_evolution

history = solve_mathler_with_evolution("26+3*4")
for i, res in enumerate(history, 1):
    print(i, res.guess, res.is_valid, res.is_correct, [c.name for c in res.feedback])
