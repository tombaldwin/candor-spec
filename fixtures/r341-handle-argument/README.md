# R341 — an effect HANDLE consumed as an ARGUMENT, not as a receiver

    candor-scan candor-spec/fixtures/r341-handle-argument --json

    a_method       ['Fs']     f.read_to_string(..)              method on a File param
    b_ufcs         ABSENT     Read::read_to_string(&mut f, ..)  same call, UFCS spelling
    c_iocopy       ABSENT     std::io::copy(&mut f, sink)
    d_from_reader  ABSENT     serde_json::from_reader(f)
    e_bufreader    ABSENT     BufReader::new(f).lines()
    n_method       ['Net']    s.write_all(..)                   method on a TcpStream param
    n_ufcs         ABSENT     Write::write_all(&mut s, ..)      same call, UFCS spelling
    x_cmd_method   ['Exec']   c.spawn()
    z_child_wait   ['Exec']   c.wait()
    z_child_ufcs   ['Exec']   Child::wait_with_output(c)        Exec is NOT affected

`reported: 5 of analyzed 10`.

## Why Exec is unaffected, and why that is the interesting part

Exec's rule keys on the TYPE PREFIX of the callee path, so `std::process::Child::wait_with_output`
matches whether the handle is a receiver or an argument. `Fs` and `Net` on a std handle are reached
through a `Read`/`Write` trait method, whose UFCS spelling puts the handle in argument position and
names a TRAIT, not the handle's type.

So this is not "candor cannot see arguments" — R334 already added `Call::entropy_arg` for exactly
that. It is narrower: the effect is a property of the ARGUMENT'S TYPE, and only the receiver position
currently gets typed.

## Not fixable by R334's mechanism

R334 matches an IDENT (`OsRng`/`SysRng`) because the OS entropy source is a value with no acquisition
call. A `File` is not: `File::open` is already charged, so charging every mention of a `File`-typed
value would double-count and would fabricate on `BufReader::new(cursor)`. The discriminator has to be
the argument's resolved TYPE, from `seed_vars`, joined with a callee list. Design and price it first.
