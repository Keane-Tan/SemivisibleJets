import calc_dark_params as cdp
from colorama import Fore, init
import os
from load_yaml_config import load_yaml_config
from xsec_from_dict import xsec_from_dict


class WriteGenSimFragment(object):
    """
    Write GEN-SIM fragment for job and return its path.
    """

    def __init__(self, config, GS_dir):
        """ Load YAML config into a dictionary and assign values to variables for cleanliness """
        _config = load_yaml_config(config)

        # Reset text colours after colourful print statements
        init(autoreset=True)

        self.model_name = _config['model_name']
        self.m_med = _config['m_med']
        self.m_d = _config['m_d']
        self.n_f = _config['n_f']
        self.r_inv = _config['r_inv']
        self.x_sec_mg = _config['x_sec_mg']
        self.alpha_d = _config['alpha_d']
        self.process_type = _config['process_type']

        self.GS_dir = GS_dir

        # Run everything
        self.set_dark_params()
        self.get_lambda_d()
        self.get_xsec()
        self.out_file = self.write_fragment()

    def set_dark_params(self):
        self.n_c = 2
        self.m_dark_meson = 2 * self.m_d
        # Calculate mass of stable dark matter particles
        self.m_dark_stable = self.m_d - 0.1

    def get_lambda_d(self):
        """ Calculate Lambda_d (confinement scale) """
        if isinstance(self.alpha_d, str):
            _Lambda_d = cdp.calc_lambda_d_from_str(self.n_c, self.n_f, self.alpha_d, self.m_dark_meson)
        else:
            _Lambda_d = cdp.calc_lambda_d(self.n_c, self.n_f, self.alpha_d)
        self.Lambda_d = round(_Lambda_d, 4)
        print Fore.MAGENTA + "Confinement scale Lambda_d =", self.Lambda_d

        # Rescale Lambda_d if too low (should be >= m_d), then recalc alpha_d
        #if Lambda_d < m_d:
        #    Lambda_d = 1.1 * m_d
        #    alpha_d = cdp.calc_alpha_d(n_c, n_f, Lambda_d)
        #    print Fore.MAGENTA + "Recalculated alpha_d =", alpha_d

    def get_xsec(self):
        """ Get cross section from dictionary if possible to replace value calculated by MadGraph """
        if self.process_type == 's-channel':
            self.x_sec = xsec_from_dict(os.path.join(os.environ['SVJ_TOP_DIR'], 'utils/xsecs_{}.yaml'.format(self.process_type)), self.m_med)
            print Fore.CYAN + "Taking cross section from dictionary instead of MadGraph's calculation..."
        else:
            self.x_sec = self.x_sec_mg

    def calc_remaining_br(self, n_quarks):
        # Can expand this in the future to take the running b- and c-quark masses into account
        remain_br = (1.0 - self.r_inv) / float(n_quarks)
        br_helper_str = "democratically allocating remaining BR (1 - r_inv)/{}".format(n_quarks)
        return remain_br, br_helper_str

    def write_fragment(self):
        """ Actually write the gen fragment """
        out_file = os.path.join(self.GS_dir, "{}_GS_fragment.py".format(self.model_name))
        f = open(out_file, "w")

        f.write("""import FWCore.ParameterSet.Config as cms
from Configuration.Generator.Pythia8CommonSettings_cfi import *
from Configuration.Generator.Pythia8CUEP8M1Settings_cfi import *
from Configuration.Generator.Pythia8aMCatNLOSettings_cfi import *
generator = cms.EDFilter("Pythia8HadronizerFilter",
    maxEventsToPrint = cms.untracked.int32(1),
    pythiaPylistVerbosity = cms.untracked.int32(1),
    filterEfficiency = cms.untracked.double(1.0),
    pythiaHepMCVerbosity = cms.untracked.bool(False),
    crossSection = cms.untracked.double({cross_section:f}),
    comEnergy = cms.double(13000.),
    PythiaParameters = cms.PSet(
        pythia8CommonSettingsBlock,
        pythia8CUEP8M1SettingsBlock,
        pythia8aMCatNLOSettingsBlock,
        JetMatchingParameters = cms.vstring(
            'JetMatching:setMad = off', # if 'on', merging parameters are set according to LHE file
            'JetMatching:scheme = 1', # 1 = scheme inspired by Madgraph matching code
            'JetMatching:merge = on', # master switch to activate parton-jet matching. when off, all external events accepted
            'JetMatching:jetAlgorithm = 2', # 2 = SlowJet clustering
            'JetMatching:etaJetMax = 5.', # max eta of any jet
            'JetMatching:coneRadius = 1.0', # gives the jet R parameter
            'JetMatching:slowJetPower = 1', # -1 = anti-kT algo, 1 = kT algo. Only kT w/ SlowJet is supported for MadGraph-style matching
            'JetMatching:qCut = 100.', # this is the actual merging scale. should be roughly equal to xqcut in MadGraph
            'JetMatching:nJetMax = 2', # number of partons in born matrix element for highest multiplicity
            'JetMatching:doShowerKt = off', # off for MLM matching, turn on for shower-kT matching
            ),
""".format(cross_section=self.x_sec))

        f.write("""
        processParameters = cms.vstring(
""")

        if self.process_type == 's-channel':
            f.write("""
            '4900023:m0 = {}', # explicitly stating Z' mass in case it's not picked up properly by Pythia""".format(self.m_med))
        elif self.process_type == 't-channel':
            f.write("""
            # ADD SHIT HERE""")

        remain_br, br_helper_str = self.calc_remaining_br(5)
        f.write("""
            '4900101:m0 = {m_dark_quark:.0f}', # explicitly stating dark quark mass in case it's not picked up properly by Pythia
            '4900113:m0 = {m_dark_meson:.0f}', # Dark meson mass. PDGID corresponds to rhovDiag HV spin-1 meson that can decay into SM particles
            '51:m0 = {m_dark_stable:.1f}', # Stable dark particle mass. PDGID corresponds to spin-0 dark matter
            '51:isResonance = false',
            '4900113:oneChannel = 1 {r_inv:.3f} 51 -51', # Dark meson decay into stable dark particles with branching fraction r_inv
            '4900113:addChannel = 1 {remain_BR:.3f} 91 1 -1', # Dark meson decay into down quarks, {sm_decay_helper}
            '4900113:addChannel = 1 {remain_BR:.3f} 91 2 -2', # Dark meson decay into up quarks, {sm_decay_helper}
            '4900113:addChannel = 1 {remain_BR:.3f} 91 3 -3', # Dark meson decay into strange quarks, {sm_decay_helper}
            '4900113:addChannel = 1 {remain_BR:.3f} 91 4 -4', # Dark meson decay into charm quarks, {sm_decay_helper}
            '4900113:addChannel = 1 {remain_BR:.3f} 91 5 -5', # Dark meson decay into bottom quarks, {sm_decay_helper}
""".format(m_dark_quark=self.m_d, m_dark_meson=self.m_dark_meson, m_dark_stable=self.m_dark_stable,
           r_inv=self.r_inv, remain_BR=remain_br, sm_decay_helper=br_helper_str)
        )

        f.write(self.get_extra_decays())
        f.write("""
            #'HiddenValley:ffbar2Zv = on', # production of f fbar -> Zv (4900023). it works only in the case of narrow width approx
            'HiddenValley:fragment = on', # enable hidden valley fragmentation
            'HiddenValley:Ngauge = 2', # dark sector is SU(2)
            #'HiddenValley:spinFv = 0', # spin of the HV partners of the SM fermions
            'HiddenValley:FSR = on', # enable final-state shower of HV gammav
            #'HiddenValley:NBFlavRun = 0', # number of bosonic flavor for running
            #'HiddenValley:NFFlavRun = 2', # number of fermionic flavor for running
            'HiddenValley:alphaOrder = 1', # order at which running coupling runs
            'HiddenValley:Lambda = {Lambda_dark:.2f}', # parameter used for running coupling
            'HiddenValley:nFlav = {nFlav:.0f}', # this dictates what kind of hadrons come out of the shower, if nFlav = 2, for example, there will be many different flavor of hadrons
            'HiddenValley:pTminFSR = {pTminFSR:.2f}', # cutoff for the showering, should be roughly confinement scale
            #'TimeShower:nPartonsInBorn = 2', # number of coloured particles (before resonance decays) in born matrix element
            ),
        parameterSets = cms.vstring('pythia8CommonSettings',
                                    'pythia8CUEP8M1Settings',
                                    'pythia8aMCatNLOSettings',
                                    'processParameters',
                                    'JetMatchingParameters'
                                    )
    )
)
""".format(Lambda_dark=self.Lambda_d, nFlav=self.n_f, pTminFSR=1.1*self.Lambda_d))

        f.write(self.insert_filters())
        f.close()

        return out_file

    def get_extra_decays(self):
        """ Compile string to include extra dark mesons and their decays, depending on value of n_f """
        if self.n_f == 1:
            ret = """
            'HiddenValley:probVector = 0.', # ratio of number of vector mesons over scalar meson"""
        elif self.n_f == 2:
            br_bc, helper_bc = self.calc_remaining_br(2)
            br_all_quarks, helper_all_quarks = self.calc_remaining_br(5)
            ret = """
            '4900111:m0 = {m_dark_meson:.0f}', # Dark meson mass. PDGID corresponds to pivDiag HV spin-0 meson that can decay into SM particles
            '4900211:m0 = {m_dark_meson:.0f}', # Dark meson mass. PDGID corresponds to pivUp HV spin-0 meson that is stable and invisible
            '4900213:m0 = {m_dark_meson:.0f}', # Dark meson mass. PDGID corresponds to rhovUp HV spin-1 meson that is stable and invisible
            '53:m0 = {m_dark_stable:.1f}', # Stable dark particle mass. PDGID corresponds to spin-1 dark matter
            '53:isResonance = false',
            '4900111:oneChannel = 1 {r_inv:.3f} 0 51 -51', # Dark meson decay into stable dark particles with branching fraction r_inv
            '4900111:addChannel = 1 {remain_BR_c:.5f} 91 4 -4', # Dark meson decay into c quarks with BR set by running mass
            '4900111:addChannel = 1 {remain_BR_b:.5f} 91 5 -5', # Dark meson decay into b quarks with BR set by running mass
            '4900211:oneChannel = 1 {r_inv:.3f} 0 51 -51', # Dark meson decay into stable dark particles with branching fraction r_inv
            '4900211:addChannel = 1 {remain_BR_c:.5f} 91 4 -4', # Dark meson decay into c quarks with BR set by running mass
            '4900211:addChannel = 1 {remain_BR_b:.5f} 91 5 -5', # Dark meson decay into b quarks with BR set by running mass
            '4900213:oneChannel = 1 {r_inv:.3f} 0 53 -53', # Dark meson decay into stable dark particles with branching fraction r_inv
            '4900213:addChannel = 1 {remain_BR_democ:.3f} 91 1 -1', # Dark meson decay into down quarks, {sm_decay_helper}
            '4900213:addChannel = 1 {remain_BR_democ:.3f} 91 2 -2', # Dark meson decay into up quarks, {sm_decay_helper}
            '4900213:addChannel = 1 {remain_BR_democ:.3f} 91 3 -3', # Dark meson decay into strange quarks, {sm_decay_helper}
            '4900213:addChannel = 1 {remain_BR_democ:.3f} 91 4 -4', # Dark meson decay into charm quarks, {sm_decay_helper}
            '4900213:addChannel = 1 {remain_BR_democ:.3f} 91 5 -5'# Dark meson decay into bottom quarks, {sm_decay_helper}
            'HiddenValley:probVector = 0.75', # ratio of number of vector mesons over scalar meson
""".format(m_dark_meson=self.m_dark_meson, m_dark_stable=self.m_dark_stable, r_inv=self.r_inv,
           remain_BR_c=br_bc, remain_BR_b=br_bc, remain_BR_democ=br_all_quarks, sm_decay_helper=helper_all_quarks)
            # sort out running masses and BR calculation for 4900111 and 4900211 to cc/bb
        else:
            raise ValueError("The value of n_f = {} specified is not allowed. Please choose either n_f = 1 or n_f = 2".format(self.n_f))
        return ret

    def insert_filters(self):
        """ Include Z2 symmmetry filter (enforce pair production of stable dark particles)
        and dark quark filter (reject events where Z' decays directly to SM particles) """
        ret = """
darkhadronZ2filter = cms.EDFilter("MCParticleModuloFilter",
    moduleLabel = cms.InputTag("generator"),
    absID = cms.bool(True),
    multipleOf = cms.uint32({two_n_dark_stable:.0f}), # 2x number of stable dark particles
    particleIDs = cms.vint32(51{extra_dark_stable}) # PDGIDs of stable dark particles
)

darkquarkFilter = cms.EDFilter("MCParticleModuloFilter",
    status = cms.int32(23),
    min = cms.uint32(2),
    moduleLabel = cms.InputTag("generator"),
    absID = cms.bool(True),
    multipleOf = cms.uint32(2),
    particleIDs = cms.vint32(4900101) # PDGID of dark quark
)
""".format(two_n_dark_stable=2*self.n_f, extra_dark_stable=', 53' if self.n_f == 2 else '')
        return ret


# TO DO: ADD SUPPORT FOR CALCULATING BR FOR C AND B BASED ON RUNNING MASSES
