import inspect
from pysb import *

def del_rule(model, rname):
    """delete rules by name 'rname'"""
    idx = [i for i,r in enumerate(model.rules) if r.name == rname][0]
    model.rules.pop(idx)

def report_extra_parms(model):
    """report the parameters that are not involved in any rules"""
    pass


def alias_model_components(model=None):
    """
    """
    if model is None:
        model = SelfExporter.default_model
    caller_globals = inspect.currentframe().f_back.f_globals
    components = dict((c.name, c) for c in model.all_components())
    caller_globals.update(components)

def two_step_mod(Enz, Sub, Prod, klist,  site='bf'):
    """Automation of the Enz + Sub <> Enz:Sub >> Enz + Prod two-step catalytic reaction.
    This function assumes that there is a site named 'bf' (bind site for fxn)
    which it uses by default. This also assume Enz returns to its original state.
    In an aim for simplicity, site 'bf' need not be passed when calling the function by
    the reactants, but THE FULL STATE OF THE PRODUCT must be specified"""
    
    kf, kr, kc = klist #forward, reverse, catalytic
    
    # FIXME: this will fail if the argument passed is a Complex object. 

    r1_name = 'cplx_%s_%s' % (Sub.monomer.name, Enz.monomer.name)
    r2_name = 'diss_%s_via_%s' % (Prod.monomer.name, Enz.monomer.name)
    
    assert site in Enz.monomer.sites_dict, \
        "Required site %s not present in %s as required"%(site, Enz.monomer.name)
    assert site in Sub.monomer.sites_dict, \
        "Required site %s not present in %s as required"%(site, Sub.monomer.name)

    # make the intermediate complex components
    etmpdict = Enz.site_conditions.copy()
    stmpdict = Sub.site_conditions.copy()
    
    etmpdict[site] = 1
    stmpdict[site] = 1

    EnzCplx = Enz.monomer(etmpdict)
    SubCplx = Sub.monomer(stmpdict)

    # add the 'bf' site to the patterns
    Enz.site_conditions[site] = None
    Sub.site_conditions[site] = None

    # now that we have the complex elements formed we can write the first step rule
    Rule(r1_name, Enz + Sub <> EnzCplx % SubCplx, kf, kr)
    
    # and finally the rule for the catalytic transformation
    Rule(r2_name, EnzCplx % SubCplx >> Enz + Prod, kc)

def two_step_conv(Sub1, Sub2, Prod, klist, site='bf'):
    """Automation of the Sub1 + Sub2 <> Sub1:Sub2 >> Prod two-step reaction (i.e. dimerization).
    This function assumes that there is a site named 'bf' (bind site for fxn)
    which it uses by default. Site 'bf' need not be passed when calling the function."""

    kf, kr, kc = klist
    
    r1_name = 'cplx_%s_%s' % (Sub2.monomer.name, Sub1.monomer.name)
    r2_name = 'cplx_%s_via_%s__%s' % (Prod.monomer.name, Sub1.monomer.name, Sub2.monomer.name)
    
    assert site in Sub1.monomer.sites_dict, \
        "Required site %s not present in %s as required"%(site, Sub1.monomer.name)
    assert site in Sub2.monomer.sites_dict, \
        "Required site %s not present in %s as required"%(site, Sub2.monomer.name)

    # make the intermediate complex components
    s1tmpdict = Sub1.site_conditions.copy()
    s2tmpdict = Sub2.site_conditions.copy()
    
    s1tmpdict[site] = 1
    s2tmpdict[site] = 1

    Sub1Cplx = Sub1.monomer(s1tmpdict)
    Sub2Cplx = Sub2.monomer(s2tmpdict)

    # add the site to the patterns
    Sub1.site_conditions[site] = None
    Sub2.site_conditions[site] = None

    # now that we have the complex elements formed we can write the first step rule
    Rule(r1_name, Sub1 + Sub2 <> Sub1Cplx % Sub2Cplx, kf, kr)
    
    # and finally the rule for the catalytic transformation
    Rule(r2_name, Sub1Cplx % Sub2Cplx >> Prod, kc)

def simple_dim(Sub, Prod, klist, site='bf'):
    """ Convert two Sub species into one Prod species:
    Sub + Sub <> Prod
    """
    kf, kr = klist
    r1_name = 'dimer_%s_to_%s'%(Sub.monomer.name, Prod.monomer.name)
    assert site in Sub.monomer.sites_dict, \
        "Required site %s not present in %s as required"%(site, Sub.monomer.name)

    # create the sites for the monomers
    Sub.site_conditions[site] = None

    # combine the monomers into a product step rule
    Rule(r1_name, Sub + Sub <> Prod, kf, kr)

def pore_species(Subunit, size):
    """
    Generate a single species representing a homomeric pore, composed
    of <size> copies of <Subunit> bound together in a ring, with bonds
    formed between bh3 of one unit and d2 of the next.
    """

    #FIXME: the sites here are hard-coded and named _bh3_ and _d2_
    #not generic and perhaps misleading?
    M = Subunit.monomer
    sc = Subunit.site_conditions
    if size == 0:
        raise ValueError("size must be an integer greater than 0")
    if size == 1:
        Pore = M(sc, bh3=None, d2=None)
    elif size == 2:
        Pore = M(sc, bh3=1, d2=None) % M(sc, d2=1, bh3=None)
    else:
        Pore = ComplexPattern([], None, match_once=True)
        for i in range(1, size+1):
            Pore %= M(sc, bh3=i, d2=i%size+1)
    return Pore

def pore_assembly(Subunit, size, rates):
    """
    Generate rules to chain identical MonomerPatterns <Subunit> into
    increasingly larger pores of up to <size> units, using sites bh3
    and d2 to bind the units to each other.
    """
    rules = []
    for i in range(2, size + 1):
        M = pore_species(Subunit, 1)
        S1 = pore_species(Subunit, i-1)
        S2 = pore_species(Subunit, i)
        rules.append(Rule('%s_pore_assembly_%d' % (Subunit.monomer.name, i),
                          M + S1 <> S2, *rates[i-2]))
    return rules

def transport(Subunit, Source, Dest, rates, site='bf'):
    #Rule('Bax_to_mem', Bax(bf = None, state = 'C') <> Bax(bf=None, state = 'M'), kbaxCbaxMf, kbaxCbaxMr)
    pass

def pore_transport(Subunit, Source, Dest, min_size, max_size, rates, site='bf'):
    """
    Generate rules to transport MonomerPattern <Source> to <Dest>
    through any of a series of pores of at least <min_size> and at
    most <max_size> subunits, as defined by pore_assembly.  Implicitly
    uses site 'bf' on both Subunit and Source to bind to each other.
    """
    assert site in Source.monomer.sites_dict, \
        "Required site %s not present in %s as required"%(site, Source.monomer.name)
    assert site in Dest.monomer.sites_dict, \
        "Required site %s not present in %s as required"%(site, Dest.monomer.name)

    for i in range(min_size, max_size+1):
        Pore = pore_species(Subunit, i)
        # require all pore subunit bf sites to be empty for Pore match
        for mp in Pore.monomer_patterns:
            mp.site_conditions[site] = None
        SM = Source.monomer
        ssc = Source.site_conditions
        DM = Dest.monomer
        dsc = Dest.site_conditions

        r1_name = '%s_pore_%d_transport_%s_cplx' % (SM.name, i, Subunit.monomer.name)
        r2_name = '%s_pore_%d_transport_%s_dssc' % (SM.name, i, Subunit.monomer.name)

        rule_rates = rates[i-min_size]
        CPore = Pore._copy()
        source_bonds = range(i+1, i+1+i)
        for b in range(i):
            CPore.monomer_patterns[b].site_conditions[site] = source_bonds[b]
        Complex = CPore % SM(ssc, bf=source_bonds)
        Rule(r1_name, Pore + SM(ssc, bf=None) <> Complex, *rule_rates[0:2])
        Rule(r2_name, Complex >> Pore + DM(dsc, bf=None), rule_rates[2])

def one_step_conv(Sub1, Sub2, Prod, klist, site='bf'):
    """ Convert two Sub species into one Prod species:
    Sub + Sub <> Prod
    """
    kf, kr = klist
    r1_name = 'conv_%s_%s_to_%s'%(Sub1.monomer.name, Sub2.monomer.name, Prod.monomer.name)
    assert site in Sub1.monomer.sites_dict, \
        "Required site %s not present in %s as required"%(site, Sub.monomer.name)
    assert site in Sub2.monomer.sites_dict, \
        "Required site %s not present in %s as required"%(site, Sub.monomer.name)
    # create the sites for the monomers

    Sub1.site_conditions[site] = None
    Sub2.site_conditions[site] = None

    # combine the monomers into a product step rule
    Rule(r1_name, Sub1 + Sub2 <> Prod, kf, kr)
    
def simple_bind(Sub1, Sub2, klist, site='bf'):
    """Automation of the Sub1 + Sub2 <> Sub1:Sub2 one-step complex formation. 
    This function assumes that there is a site named 'bf' which, for simplicity
    need not be passed"""
    
    kf, kr = klist
    
    # FIXME: this will fail if the argument passed is a complex... 
    r1_name = 'cplx_%s_%s' % (Sub1.monomer.name, Sub2.monomer.name)
    
    assert site in Sub1.monomer.sites_dict, \
        "Required site %s not present in %s as required"%(site, Sub1.monomer.name)
    assert site in Sub2.monomer.sites_dict, \
        "Required site %s not present in %s as required"%(site, Sub2.monomer.name)
    
    # create the site conditions for the complex
    s1tmpdict = Sub1.site_conditions.copy()
    s2tmpdict = Sub2.site_conditions.copy()
    
    s1tmpdict[site] = 1
    s2tmpdict[site] = 1

    Sub1Cplx = Sub1.monomer(s1tmpdict)
    Sub2Cplx = Sub2.monomer(s2tmpdict)

    # create the sites for the monomers
    Sub1.site_conditions[site] = None
    Sub2.site_conditions[site] = None
    # now that we have the complex elements formed we can write the first step rule
    Rule(r1_name, Sub1 + Sub2 <> Sub1Cplx % Sub2Cplx, kf, kr)

inhibit = simple_bind #alias for simplebind

#FIXME: pass klist of sorts?
def simple_bind_table(bindtable, lmodel, site='bf'):
    """This assumes that the monomers passed are in their desired state without
    the 'bf' site, which will be used for binding.
    bindtable is a list of lists denoting the reactions between two types of reactants
    as follows:

    bindtable[0]: [                  reactypeA0(args), reactypeA1(args)... reactypeAN(args)]
    bindtable[1]: [reactypeB0(args), 'parmfamA0B0',    'parmfamA1B0'...    'parmfamANB0'   ]
    bindtable[2]: [reactypeB1(args), 'parmfamA0B1',    'parmfamA1B1'...    'parmfamANB1'   ]
    
    the variable 'lmodel' is the model passed for local lookup of parameter variables
    """

    # parse the list, extract reactants, products and parameter families
    #first line is one set of reactants
    react0 = bindtable[0]
    react0st = bindtable[1]
    react1 = [row[0] for row in bindtable[2:]]
    react1st = [row[1] for row in bindtable[2:]]

    # Notice this makes intrxns of size/index intrxns[react1][react0]
    intrxns = [row[2:] for row in bindtable[2:]]
    
    # Add the bf sites to the reactant states dict
    # NOTE: this will reset the value if it is already set.
    # Build the prod states dict from react dicts, change bf to 1
    prod0st = []
    prod1st = []
    for d in react0st:
        d[site] = None
        prod0st.append(d.copy())
    for d in react1st:
        d[site] = None
        prod1st.append(d.copy())
    for d in prod0st:
        d[site] = 1
    for d in prod1st:
        d[site] = 1
    
    # loop over interactions
    for i in range(0, len(react1)):
        for j in range(0, len(react0)):
            if intrxns[i][j] is True:
                # build the name of the forward/reverse parameters
                # FIXME: make the rate passing uniform with the simple fxns
                sparamf = react1[i].name.lower()+react0[j].name.lower()+'f'
                sparamr = react1[i].name.lower()+react0[j].name.lower()+'r'
                kf = lmodel.parameter(sparamf)
                kr = lmodel.parameter(sparamr)
                # rule name
                rname = 'cplx_%s_%s' % (react1[i].name, react0[j].name)
                # create the rule
                #print "Generating  %s:%s complex"%(react1[i].name, react0[j].name)
                Rule(rname, react1[i](react1st[i]) + react0[j](react0st[j]) <>
                     react1[i](prod1st[i]) % react0[j](prod0st[j]), 
                     kf, kr)
    
    
