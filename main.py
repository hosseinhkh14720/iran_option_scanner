from scanner import scan
from report import build

def main():
    try:
        rows = scan()
        path = build(rows)
        print(f"OK: {path} | scanned={len(rows)}")
    except Exception as e:
        print("SCAN ERROR:", e)
        build([], error=str(e))

if __name__ == "__main__":
    main()
