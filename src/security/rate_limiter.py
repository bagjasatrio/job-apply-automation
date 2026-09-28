import os
import time
import random
from typing import Tuple, Optional

class SmartRateLimiter:
    def __init__(
        self,
        min_delay_seconds: int = 180,
        max_delay_seconds: int = 420,
        state_file: str = ".last_sent_timestamp"
    ):
        self.min_delay_seconds = min_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.state_file = os.path.abspath(state_file)
        self.current_target_delay = self._generate_jitter()
        self._last_sent_ts: float = self._load_last_sent()

    def _generate_jitter(self) -> int:
        return random.randint(self.min_delay_seconds, self.max_delay_seconds)

    def _load_last_sent(self) -> float:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return float(f.read().strip())
            except Exception:
                pass
        return 0.0

    def record_sent(self, fake_timestamp: Optional[float] = None):
        ts = fake_timestamp if fake_timestamp is not None else time.time()
        self._last_sent_ts = ts
        try:
            with open(self.state_file, "w") as f:
                f.write(str(ts))
        except Exception:
            pass
        self.current_target_delay = self._generate_jitter()

    def can_send_now(self) -> Tuple[bool, int]:
        if self._last_sent_ts == 0.0:
            return True, 0

        elapsed = time.time() - self._last_sent_ts
        if elapsed >= self.current_target_delay:
            return True, 0

        remaining = int(self.current_target_delay - elapsed)
        return False, max(1, remaining)

    def wait_cooldown(self, interactive: bool = True) -> bool:
        can_send, remaining = self.can_send_now()
        if can_send:
            return True

        mins = remaining // 60
        secs = remaining % 60
        time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

        print(f"\n[Smart Rate Limiter] 🛡️ Jeda keamanan aktif ({time_str} tersisa).")
        print("Menjaga reputasi domain email dari deteksi bot/spam filter Google & HRD.")

        if interactive:
            choice = input("Pilihan: [T]unggu jeda aman selesai, [B]ypass jeda, atau [Batal]? (t/b/c) [Default: t]: ").strip().lower()
            if choice == "b":
                print("Jeda dilewati (Bypass).")
                return True
            elif choice == "c":
                print("Pengiriman dibatalkan.")
                return False

        print(f"Menunggu {remaining} detik...", end="", flush=True)
        try:
            while remaining > 0:
                time.sleep(1)
                remaining -= 1
                if remaining % 10 == 0 or remaining <= 5:
                    print(f" {remaining}s", end="", flush=True)
            print("\nJeda aman selesai. Melanjutkan proses pengiriman.")
            return True
        except KeyboardInterrupt:
            print("\nJeda dibatalkan oleh pengguna.")
            return False
