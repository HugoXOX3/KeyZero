import requests
from bit import Key
from time import sleep, time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count

# List of blockchain APIs to check balances
BLOCKCHAIN_APIS = [
    "https://blockchain.info/q/getreceivedbyaddress/{address}",  # Blockchain.info
    "https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance",  # BlockCypher
    "https://blockstream.info/api/address/{address}",  # Blockstream
]

# Cache file for storing progress
CACHE_FILE = "cache.txt"

if not os.path.exists(CACHE_FILE):
    open(CACHE_FILE, "w+").close()

class Btcbf:
    def __init__(self):
        self.start_t = 0
        self.prev_n = 0
        self.cur_n = 0
        self.start_n = 0
        self.end_n = 0
        self.seq = False
        self.privateKey = None
        self.start_r = 0
        self.loaded_addresses = self._load_addresses("address.txt")
        self.cores = cpu_count()

    def _load_addresses(self, filename):
        """Load addresses from a file and remove invalid entries."""
        if not os.path.exists(filename):
            open(filename, "w+").close()
            return set()
        with open(filename, "r") as f:
            addresses = [x.strip() for x in f.readlines() if x.strip() and "wallet" not in x]
        return set(addresses)

    def speed(self):
        """Display the current speed and progress."""
        while True:
            if self.cur_n != 0:
                cur_t = time()
                n = self.cur_n
                if self.prev_n == 0:
                    self.prev_n = n
                elapsed_t = cur_t - self.start_t
                print(
                    f"Current n: {n}, Rate: {abs(n - self.prev_n) // 2}/s, "
                    f"Elapsed: [{elapsed_t // 3600}:{elapsed_t // 60 % 60}:{int(elapsed_t % 60)}], "
                    f"Total: {n - self.start_r}",
                    end="\r"
                )
                self.prev_n = n
                if self.seq:
                    with open(CACHE_FILE, "w") as f:
                        f.write(f"{self.cur_n}-{self.start_r}-{self.end_n}")
            sleep(2)

    def check_balance(self, address):
        """Check the balance of a Bitcoin address using multiple APIs."""
        for api in BLOCKCHAIN_APIS:
            try:
                url = api.format(address=address)
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json() if "json" in response.headers.get("Content-Type", "") else response.text
                    if api == BLOCKCHAIN_APIS[0]:  # Blockchain.info
                        if int(data) > 0:
                            return True
                    elif api == BLOCKCHAIN_APIS[1]:  # BlockCypher
                        if data.get("balance", 0) > 0:
                            return True
                    elif api == BLOCKCHAIN_APIS[2]:  # Blockstream
                        if data.get("chain_stats", {}).get("funded_txo_sum", 0) > 0:
                            return True
            except (requests.RequestException, ValueError):
                continue
        return False

    def random_brute(self, n):
        """Randomly generate a Bitcoin key and check its balance."""
        self.cur_n = n
        key = Key()
        if key.address in self.loaded_addresses or self.check_balance(key.address):
            self._save_found_key(key)
            exit()

    def sequential_brute(self, n):
        """Sequentially generate Bitcoin keys and check their balances."""
        self.cur_n = n
        key = Key().from_int(n)
        if key.address in self.loaded_addresses or self.check_balance(key.address):
            self._save_found_key(key)
            exit()

    def _save_found_key(self, key):
        """Save the found key to a file."""
        print("\nWow! Matching address found!!")
        print(f"Public Address: {key.address}")
        print(f"Private Key: {key.to_wif()}")
        with open("foundkey.txt", "a") as f:
            f.write(f"{key.address}\n{key.to_wif()}\n")
        sleep(500)
        exit()

    def num_of_cores(self):
        """Get the number of CPU cores to use from the user."""
        available_cores = cpu_count()
        cores = input(
            f"\nNumber of available cores: {available_cores}\n"
            f"How many cores to use? (Leave empty to use all): "
        ).strip()
        if cores == "":
            self.cores = available_cores
        elif cores.isdigit():
            cores = int(cores)
            if 0 < cores <= available_cores:
                self.cores = cores
            else:
                print(f"Invalid number of cores. Using {available_cores} cores.")
                self.cores = available_cores
        else:
            print("Invalid input. Using all available cores.")
            self.cores = available_cores
        return self.cores

    def get_user_input(self):
        """Get user input for the desired operation."""
        user_input = input(
            "\nWhat do you want to do?\n"
            "   [1]: Generate random key pair\n"
            "   [2]: Generate public address from private key\n"
            "   [3]: Brute force Bitcoin (offline mode)\n"
            "   [4]: Brute force Bitcoin (online mode)\n"
            "   [0]: Exit\n"
            "Type something> "
        )
        if user_input == "1":
            self._generate_random_address()
        elif user_input == "2":
            self._generate_address_from_key()
        elif user_input == "3":
            self._offline_brute_force()
        elif user_input == "4":
            self._online_brute_force()
        elif user_input == "0":
            print("Exiting...")
            exit()
        else:
            print("Invalid input. Exiting...")
            exit()

    def _generate_random_address(self):
        """Generate a random Bitcoin key pair."""
        key = Key()
        print(f"\nPublic Address: {key.address}")
        print(f"Private Key: {key.to_wif()}")
        input("\nPress Enter to exit")
        exit()

    def _generate_address_from_key(self):
        """Generate a Bitcoin address from a private key."""
        self.privateKey = input("\nEnter Private Key> ")
        try:
            key = Key(self.privateKey)
            print(f"\nPublic Address: {key.address}")
            print("\nYour wallet is ready!")
        except:
            print("\nIncorrect key format.")
        input("Press Enter to exit")
        exit()

    def _offline_brute_force(self):
        """Perform offline brute force attack."""
        method_input = input(
            "\nChoose attack method:\n"
            "   [1]: Random attack\n"
            "   [2]: Sequential attack\n"
            "   [0]: Exit\n"
            "Type something> "
        )
        if method_input == "1":
            self._random_offline_attack()
        elif method_input == "2":
            self._sequential_offline_attack()
        else:
            print("Exiting...")
            exit()

    def _online_brute_force(self):
        """Perform online brute force attack."""
        method_input = input(
            "\nChoose attack method:\n"
            "   [1]: Random attack\n"
            "   [2]: Sequential attack\n"
            "   [0]: Exit\n"
            "Type something> "
        )
        if method_input == "1":
            self._random_online_attack()
        elif method_input == "2":
            print("Sequential online attack will be available soon!")
            input("Press Enter to exit")
            exit()
        else:
            print("Exiting...")
            exit()

    def _random_offline_attack(self):
        """Perform random offline brute force attack."""
        with ThreadPoolExecutor(max_workers=self.num_of_cores()) as pool:
            print("\nStarting random offline attack...")
            self.start_t = time()
            self.start_n = 0
            for i in range(100000000000000000):
                pool.submit(self.random_brute, i)
            print("Stopping...")
            exit()

    def _sequential_offline_attack(self):
        """Perform sequential offline brute force attack."""
        if os.path.getsize(CACHE_FILE) > 0:
            with open(CACHE_FILE, "r") as f:
                r0 = f.read().split("-")
                print(f"Resuming range {r0[0]}-{r0[2]}")
                self.start_t = time()
                self.start_r = int(r0[1])
                self.start_n = int(r0[0])
                self.end_n = int(r0[2])
                self.seq = True
        else:
            range0 = input("\nEnter range in decimals (e.g., 1-100)> ")
            r0 = range0.split("-")
            r0.insert(1, r0[0])
            with open(CACHE_FILE, "w") as f:
                f.write("-".join(r0))
            self.start_t = time()
            self.start_r = int(r0[1])
            self.start_n = int(r0[0])
            self.end_n = int(r0[2])
            self.seq = True

        with ThreadPoolExecutor(max_workers=self.num_of_cores()) as pool:
            print("\nStarting sequential offline attack...")
            for i in range(self.start_n, self.end_n):
                pool.submit(self.sequential_brute, i)
            print("Stopping...")
            exit()

    def _random_online_attack(self):
        """Perform random online brute force attack."""
        with ThreadPoolExecutor(max_workers=self.num_of_cores()) as pool:
            print("\nStarting random online attack...")
            self.start_t = time()
            self.start_n = 0
            for i in range(100000000000000000):
                pool.submit(self.random_brute, i)
                sleep(0.1)
            print("Stopping...")
            exit()


if __name__ == "__main__":
    obj = Btcbf()
    try:
        t0 = threading.Thread(target=obj.get_user_input)
        t1 = threading.Thread(target=obj.speed)
        t1.daemon = True
        t0.daemon = True
        t0.start()
        t1.start()
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\n\nCtrl+C pressed. Exiting...")
        exit()
