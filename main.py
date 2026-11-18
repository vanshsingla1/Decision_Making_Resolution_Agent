
from agent import run_agent

def main():

    print("\n" + "=" * 50)
    print("       AI CUSTOMER RESOLUTION AGENT")
    print("=" * 50)

    print("\nWelcome! How can I help you today?")

    while True:

        customer_query = input("\nEnter your complaint (or type 'exit'): ").strip()

        if customer_query.lower() == "exit":
            print("\nThank you for using our resolution agent!")
            break

        if not customer_query:
            print("Please enter a valid complaint.")
            continue

        print("\nAI Agent is processing your request...\n")

        try:
            response = run_agent(customer_query)

            print("\n========== FINAL RESOLUTION ==========")
            print(response)
            print("======================================")

        except Exception as e:
            print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    main()
