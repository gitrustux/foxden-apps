// Copyright 2026 The Rustux Authors
//
// Use of this source code is governed by a MIT-style
// license that can be found in the LICENSE file or at
// https://opensource.org/licenses/MIT

//! Dice: the example app of the foxden-apps repository. Pick how many
//! dice, then Roll (or Space, or Enter); each roll is shown and printed
//! ("dice: 3 dice: 4 1 6 = 11"). It asks for no permissions.

use rustica_ui::ui::keys;
use rustica_ui::{Control, Ui};

/// A small xorshift generator, seeded from the clock
struct Rng(u64);

impl Rng {
    fn new() -> Rng {
        let t = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_nanos() as u64).unwrap_or(1);
        Rng(t | 1)
    }
    fn next(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.0 = x;
        x
    }
    /// 1 to 6
    fn die(&mut self) -> u32 {
        (self.next() % 6) as u32 + 1
    }
}

struct Dice {
    count: usize,
    rolled: Vec<u32>,
    rng: Rng,
}

impl Dice {
    fn roll(&mut self) {
        self.rolled = (0..self.count).map(|_| self.rng.die()).collect();
        let total: u32 = self.rolled.iter().sum();
        let list: Vec<String> = self.rolled.iter().map(u32::to_string).collect();
        println!("dice: {} dice: {} = {total}", self.count, list.join(" "));
    }

    fn frame(&mut self, ui: &mut Ui, _ctl: &mut Control) {
        let mut roll = false;
        for k in &ui.input.keys {
            if k.usage == keys::ENTER || k.usage == keys::SPACE {
                roll = true;
            }
        }
        ui.heading("Dice");
        ui.row(|ui| {
            for n in 1..=5 {
                let label = if n == self.count { format!("[{n}]") } else { n.to_string() };
                if ui.button(&label) {
                    self.count = n;
                    self.rolled.clear();
                }
            }
        });
        ui.space(12.0);
        if self.rolled.is_empty() {
            ui.dim_label(&format!("{} {} ready: press Roll", self.count, if self.count == 1 { "die" } else { "dice" }));
        } else {
            let faces: Vec<String> = self.rolled.iter().map(|v| format!("[ {v} ]")).collect();
            ui.heading(&faces.join("  "));
            let list: Vec<String> = self.rolled.iter().map(u32::to_string).collect();
            ui.label(&format!("{}  =  {}", list.join(" + "), self.rolled.iter().sum::<u32>()));
        }
        ui.space(12.0);
        if ui.primary_button("Roll") {
            roll = true;
        }
        if roll {
            self.roll();
        }
    }
}

fn main() {
    let mut d = Dice { count: 2, rolled: Vec::new(), rng: Rng::new() };
    if let Err(e) = rustica_ui::run("Dice", 360, 260, None, |ui, ctl| d.frame(ui, ctl)) {
        eprintln!("dice: {e}");
        std::process::exit(1);
    }
}
