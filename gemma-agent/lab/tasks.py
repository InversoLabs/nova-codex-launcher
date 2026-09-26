"""Original micro-tasks: family splits are fixed, never randomly split turns."""
TASKS = [
    dict(id="clamp", split="train", prompt="Fix clamp(x, low, high) to return x bounded inclusively by low and high.", args="x, low, high", broken="return min(low, max(high, x))", solution="return max(low, min(high, x))", cases=[([5,0,10],5),([-1,0,10],0),([11,0,10],10),([0,0,10],0)]),
    dict(id="is_even", split="train", prompt="Fix is_even(n) to return whether integer n is even, including zero and negatives.", args="n", broken="return n % 2 == 1", solution="return n % 2 == 0", cases=[([0],True),([2],True),([-4],True),([3],False)]),
    dict(id="last_item", split="train", prompt="Fix last_item(items) to return the last item, or None for an empty list.", args="items", broken="return items[0]", solution="return items[-1] if items else None", cases=[([[1,2,3]],3),([[]],None),([[0]],0)]),
    dict(id="normalize", split="train", prompt="Fix normalize(text) to strip leading/trailing whitespace and lowercase the result.", args="text", broken="return text.upper()", solution="return text.strip().lower()", cases=[(["  Hello  "],"hello"),([""],""),([" a B "],"a b")]),
    dict(id="safe_mean", split="validation", prompt="Fix safe_mean(values) to return the arithmetic mean, or 0 for an empty list.", args="values", broken="return sum(values)", solution="return sum(values) / len(values) if values else 0", cases=[([[2,4]],3),([[]],0),([[-2,2]],0),([[5]],5)]),
    dict(id="positive", split="validation", prompt="Fix positive(values) to keep strictly positive values, preserving order and duplicates.", args="values", broken="return values", solution="return [v for v in values if v > 0]", cases=[([[-1,0,2,2]], [2,2]),([[]],[]),([[-2]],[])]),
    dict(id="reverse_text", split="test", prompt="Fix reverse_text(text) to reverse the characters of the string.", args="text", broken="return text", solution="return text[::-1]", cases=[(["abc"],"cba"),([""],""),(["a b"],"b a")]),
    dict(id="within", split="test", prompt="Fix within(x, low, high) to test inclusive membership in the numeric interval.", args="x, low, high", broken="return low < x < high", solution="return low <= x <= high", cases=[([0,0,2],True),([2,0,2],True),([3,0,2],False),([1,0,2],True)]),
]

def source(task, solved=False):
    return f"def {task['id']}({task['args']}):\n    {task['solution' if solved else 'broken']}\n"

def get(task_id):
    return next(t for t in TASKS if t['id'] == task_id)
