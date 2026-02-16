# VHS Tape — AgentGuard BudgetGuard Demo
# Install: brew install vhs
# Record:  vhs examples/demo.tape

Output examples/demo.gif

Set Shell "bash"
Set FontSize 16
Set Width 900
Set Height 520
Set Theme "Catppuccin Mocha"
Set Padding 20
Set Framerate 30

Type "# AgentGuard: Stop runaway AI agent costs"
Enter
Sleep 1s

Type "pip install agentguard47"
Enter
Sleep 500ms
Type "# already installed ✓"
Enter
Sleep 1s

Type "python examples/demo_budget_kill.py"
Enter
Sleep 18s

Sleep 3s
