# EARM 1.0 MODULES
# Notice the alias_model_components function is needed to recognize the monomer and 
# parameter names in the present scope
#
# rec_to_bid: This module defines the interactions from the ligand insult (e.g. TRAIL)
#             to Bid activation as per EARM 1.0
#
# fxrcsp_to_parp: This module defines what happens after the pore is activated and 
#                 CytC and Smac are released
#
# These segments are adapted from:
# Albeck JG, Burke JM, Spencer SL, Lauffenburger DA, Sorger PK, 2008
# Modeling a Snap-Action, Variable-Delay Switch Controlling Extrinsic
# Cell Death. PLoS Biol 6(12): e299. doi:10.1371/journal.pbio.0060299
#
# http://www.plosbiology.org/article/info:doi/10.1371/journal.pbio.0060299
#
#
from pysbhelperfuncs import *

# get model components accessible in this scope
alias_model_components()

# RECEPTOR TO BID SEGMENT
def rec_to_bid(model):
    """ This is a very specific function which depends on specifically
    on the parameters and monomers of earm_1_0 to work. This function
    uses L, R, DISC, flip, C8, BAR, and Bid monomers and their
    associated parameters to generate the rules that describe Ligand
    to Receptor binding, DISC formation, Caspase8 activation and
    inhibition by flip and BAR as specified in EARM1.0.
    """
    # RECEPTOR TO tBID
    # =====================
    # tBID Activation Rules
    # ---------------------
    #        L + R <--> L:R --> DISC
    #        pC8 + DISC <--> DISC:pC8 --> C8 + DISC
    #        Bid + C8 <--> Bid:C8 --> tBid + C8
    # ---------------------
    two_step_conv(L(), R(), DISC(bf = None ), [klrf, klrr, klrc])
    two_step_mod(DISC(), C8(state='pro'), C8(bf = None, state='A'), [kdiscc8f, kdiscc8r, kdiscc8c])
    two_step_mod(C8(state='A'), Bid(state='U'), Bid(bf = None, state='T'), [kc8bidf, kc8bidr, kc8bidc])
    # ---------------------
    # Inhibition Rules
    # ---------------------
    #        flip + DISC <-->  flip:DISC  
    #        C8 + BAR <--> BAR:C8 CSPS
    # ---------------------
    simple_bind(DISC(), flip(), [kflipdiscf, kflipdiscr])
    simple_bind(BAR(), C8(state='A'), [kbarc8f, kbarc8r])
    # ---------------------

def pore_to_parp(model):
    """ This is a very specific function which depends on specifically
    on the parameters and monomers of earm_1_0 to work. This function
    uses MitoP, CytoC, Smac, Apaf, Apop, C3, C6, C8, C9, PARP, XIAP
    monomers and their associated parameters to generate the rules
    that describe CytC and Smac export from the mitochondria by the
    active pore activation of Caspase3, loopback through Caspase 6,
    and some inhibitions as specified in EARM1.0.
    """
    # FXR CASPASES CLEAVE PARP 
    # ========================
    # CytC, Smac release
    # ----------------------
    #        AMito + mCytoC <-->  AMito:mCytoC --> AMito + ACytoC  
    #        AMito + mSmac <-->  AMito:mSmac --> AMito + ASmac  
    #        ACytoC <-->  cCytoC
    #        ASmac <-->  cSmac
    # ----------------------
    #pore_transport(Subunit, Source, Dest, min_size, max_size, rates):
    pore_transport(Bax(bf=None), CytoC(state='M'), CytoC(state='C'), 4, 4, [[kbaxcytocMCf, kbaxcytocMCr, kbaxcytocMCc]]) 
    pore_transport(Bak(bf=None), CytoC(state='M'), CytoC(state='C'), 4, 4, [[kbakcytocMCf, kbakcytocMCr, kbakcytocMCc]])
    pore_transport(Bax(bf=None),  Smac(state='M'),  Smac(state='C'), 4, 4, [[kbaxsmacCAf, kbaxsmacCAr, kbaxsmacCAc]]) 
    pore_transport(Bak(bf=None),  Smac(state='M'),  Smac(state='C'), 4, 4, [[kbaksmacCAf, kbaksmacCAr, kbaksmacCAc]])
    Rule('cytocCtoM', CytoC(bf = None, state='C') <> CytoC(bf=None, state = 'A'), kcytocMcytocCf, kcytocMcytocCr)
    Rule('SmacMtoSmacC', Smac(bf = None, state='C') <> Smac(bf = None, state='A'), ksmacMsmacCf, ksmacMsmacCr)
    # ---------------------------
    # Apoptosome formation
    # ---------------------------
    #        Apaf + cCytoC <-->  Apaf:cCytoC --> aApaf + cCytoC
    #        aApaf + pC9 <-->  Apop
    #        Apop + pC3 <-->  Apop:pC3 --> Apop + C3
    # ---------------------------
    two_step_mod(CytoC(state='C'), Apaf(state='I'), Apaf(bf = None, state = 'A'), [kcytocCapaff, kcytocCapafr, kcytocCapafc])
    one_step_conv(Apaf(state='A'), C9(), Apop(bf=None), [kapafc9f, kapafc9r])
    two_step_mod(Apop(), C3(state='pro'), C3(bf = None, state='A'), [kapopc3f, kapopc3r, kapopc3c])
    # -----------------------------
    # Apoptosome related inhibitors
    # -----------------------------
    #        Apop + XIAP <-->  Apop:XIAP  
    #        cSmac + XIAP <-->  cSmac:XIAP  
    simple_bind(Apop(), XIAP(), [kapopxiapf, kapopxiapr])
    simple_bind(Smac(state='C'), XIAP(), [ksmacxiapf, ksmacxiapr])
    # ---------------------------
    # Caspase reactions (effectors, inhibitors, and loopback initiators)
    # ---------------------------
    #        pC3 + C8 <--> pC3:C8 --> C3 + C8 CSPS
    #        pC6 + C3 <--> pC6:C3 --> C6 + C3 CSPS
    #        XIAP + C3 <--> XIAP:C3 --> XIAP + C3_U CSPS
    #        PARP + C3 <--> PARP:C3 --> CPARP + C3 CSPS
    #        pC8 + C6 <--> pC8:C6 --> C8 + C6 CSPS
    # ---------------------------
    two_step_mod(C8(state='A'), C3(state='pro'), C3(bf = None, state='A'), [kc8c3f, kc8c3r, kc8c3c])
    two_step_mod(C3(state='A'), C6(state='pro'), C6(bf = None, state='A'), [kc3c6f, kc3c6r, kc3c6c])
    two_step_mod(XIAP(), C3(state = 'A'), C3(bf = None, state = 'ub'), [kxiapc3f, kxiapc3r, kxiapc3c])
    two_step_mod(C3(state = 'A'), PARP(state='U'), PARP(bf = None, state='C'), [kc3parpf, kc3parpr, kc3parpc])
    two_step_mod(C6(state='A'), C8(state='pro'), C8(bf = None, state = 'A'), [kc6c8f, kc6c8r, kc6c8c])