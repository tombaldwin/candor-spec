use std::fs;
pub struct Guard;
impl Guard { pub fn run(&self) -> usize { let _ = fs::write("/tmp/rf", "x"); 1 } }
pub struct Calm;
impl Calm { pub fn run(&self) -> usize { 7 } }

pub struct H { v: Vec<Guard>, c: Vec<Calm> }
impl H {
    pub fn base(&self)      { self.v.iter().for_each(|g| { g.run(); }); }            // control
    pub fn x_fold(&self)    { let _: usize = self.v.iter().fold(0, |a, g| a + g.run()); }
    pub fn x_try_fold(&self){ let _: Option<usize> = self.v.iter().try_fold(0usize, |a, g| Some(a + g.run())); }
    pub fn x_scan(&self)    { let _: Vec<_> = self.v.iter().scan(0, |a, g| { *a += g.run(); Some(*a) }).collect(); }
    pub fn x_enum(&self)    { for (_, g) in self.v.iter().enumerate() { g.run(); } }
    pub fn x_enumEach(&self){ self.v.iter().enumerate().for_each(|(_, g)| { g.run(); }); }
    pub fn x_zip(&self)     { for (g, _) in self.v.iter().zip([1].iter()) { g.run(); } }
    pub fn ctl_fold(&self)  { let _: usize = self.c.iter().fold(0, |a, g| a + g.run()); }
}
