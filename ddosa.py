# check for logic in osa! make sure there is none!

# make cool plots

# reduce logs to essential; marker stream on topic

# output effect

# evaluate time, estimate time to do

from dataanalysis import DataFile
#from dataanalysis import DataAnalysis,DataFile,Cache
import dataanalysis 

from pilton import heatool

import os,shutil,re,time


mcg=dataanalysis.MemCache('/sps/integral/analysis/cache/dda_global')

class DataAnalysis(dataanalysis.DataAnalysis):
    cache=mcg

#
# there are two ways to define common origin:
#   define during class declaratopm
# dynamic redefinition of the classes, like ScWData, will invalidate (hopefully) the get call, so it should be reexecuted

# there is special treatement
class ScWData(DataAnalysis):
    input_scwid=None

    def __init__(self,scwid=None):
        if scwid is not None:
            self.input_scwid=scwid

    def main(self):
        self.scwid=self.input_scwid.handle
        self.scwver=self.scwid[-3:]
        self.revid=self.scwid[:4]

        self.scwpath=os.environ['REP_BASE_PROD']+"/scw/"+self.revid+"/"+self.scwid #!!!!
        self.revdirpath=os.environ['REP_BASE_PROD']+"/scw/"+self.revid+"/rev.001" # ver?
        self.auxadppath=os.environ['REP_BASE_PROD']+"/aux/adp/"+self.revid+".001"

        if not os.path.exists(self.scwpath+"/swg.fits"):
            raise Exception("no scw data!")

class GetLUT2(DataAnalysis):
    input="LUT2_standard"

    def main(self):
        self.datafile=os.environ['REP_BASE_PROD']+"/ic/ic_10/ic/ibis/mod/isgr_3dl2_mod_0001.fits"
        #self.datafile=DataFile(os.environ['REP_BASE_PROD']+"/ic/ic_10/ic/ibis/mod/isgr_3dl2_mod_0001.fits")

class GetEcorrCalDB(DataAnalysis):
    input=["ecorr_standard_OSA10"]
    input_lut2=GetLUT2

    def main(self):
        self.godol=os.environ['REP_BASE_PROD']+"/ic/ic_10/ic/ibis/cal/ibis_isgr_gain_offset_0010.fits"
        self.supgdol=os.environ['REP_BASE_PROD']+"/ic/ic_10/ic/ibis/mod/isgr_gain_mod_0001.fits[ISGR-GAIN-MOD,1,BINTABLE]"
        self.supodol=os.environ['REP_BASE_PROD']+"/ic/ic_10/ic/ibis/mod/isgr_off2_mod_0001.fits[ISGR-OFF2-MOD,1,BINTABLE]"
        self.risedol=self.input_lut2.datafile

class ibis_isgr_energy(DataAnalysis):
    
    input_scw=ScWData()
    #input_raw_events=None
    #input_ibis_hk=None
    # can also take only isgri events

    input_ecorrdata=GetEcorrCalDB()

    version="v3"
   
    def main(self):

        remove_withtemplate("isgri_events_corrected.fits(ISGR-EVTS-COR.tpl)")
    
        construct_gnrl_scwg_grp(self.input_scw,[\
            self.input_scw.scwpath+"/isgri_events.fits[3]", \
            self.input_scw.scwpath+"/ibis_hk.fits[IBIS-DPE.-CNV]" \
        ])

        bin="/afs/in2p3.fr/throng/integral/software/spectral/ibis_isgr_energy/ibis_isgr_energy_pha2/ibis_isgr_energy"
        ht=heatool(bin)
        ht['inGRP']="og.fits"
        ht['outCorEvts']="isgri_events_corrected.fits(ISGR-EVTS-COR.tpl)"
        ht['useGTI']="n"
        ht['randSeed']=500
        ht['riseDOL']=self.input_ecorrdata.risedol
        ht['GODOL']=self.input_ecorrdata.godol
        ht['supGDOL']=self.input_ecorrdata.supgdol
        ht['supODOL']=self.input_ecorrdata.supodol
        ht['chatter']="4"
        ht.run()


        self.output_events=DataFile("isgri_events_corrected.fits")
            

class ibis_isgr_evts_tag(DataAnalysis):
    
    input_events_corrected=ibis_isgr_energy()
    input_scw=ScWData() # again, can get separate

    #input_ecorrdata=GetEcorrCalDB()

    version="v0"
   
    def main(self):

        #remove_withtemplate("isgri_events_corrected.fits(ISGR-EVTS-COR.tpl)")
    
        construct_gnrl_scwg_grp(self.input_scw,[\
            self.input_scw.scwpath+"/isgri_events.fits[3]", \
            self.input_events_corrected.output_events.path \
        ])
            #self.input_scw.scwpath+"/ibis_hk.fits[IBIS-DPE.-CNV]" \

        import_attr(self.input_scw.scwpath+"/swg.fits",['OBTSTART','OBTEND'])
        
        bin="ibis_isgr_evts_tag"
        ht=heatool(bin)
        ht['inGRP']="og.fits"
        ht['idxSwitch']=self.input_scw.revdirpath+"/idx/isgri_pxlswtch_index.fits[1]"
        ht['seleEXT']="ISGR-EVTS-COR"
        ht.run()

        self.output_events=DataFile("isgri_events_corrected.fits")

class ICRoot(DataAnalysis):
    input="standard_IC"

    version="v1"

    def main(self):
        self.icroot=os.environ['REP_BASE_PROD']+"/ic/ic_10/"
        self.icindex=os.environ['REP_BASE_PROD']+"/ic/ic_10/idx/ic/ic_master_file.fits[1]"


class IBIS_ICRoot(DataAnalysis):
    input="standard IC"

    def main(self):
        self.ibisicroot=os.environ['REP_BASE_PROD']+"/ic/ic_10/ic/ibis"

# maybe split indeed,but try to show another case
class ibis_gti(DataAnalysis):
    input_scw=ScWData()
    input_ic=ICRoot()
    #input_gticreate=gti_create()
    
    version="v2"
    def main(self):
        # horrible horrible full OSA

        open("scw.list","w").write(self.input_scw.scwid)

        if os.path.exists("obs"):
            os.rename("obs","obs."+str(time.time()))
        
        bin="og_create"
        ogc=heatool(bin)
        ogc['idxSwg']="scw.list"
        ogc['instrument']="IBIS"
        ogc['ogid']="scw_"+self.input_scw.scwid
        ogc['baseDir']="./"
        ogc.run()
        
        scwroot="scw/"+self.input_scw.scwid

        bin="ibis_gti"
        ht=heatool(bin,wd="obs/"+ogc['ogid'].value) 
        ht['swgDOL']=scwroot+"/swg_ibis.fits"
        ht['GTI_Index']="ibis_gti.fits(IBIS-GNRL-GTI-IDX.tpl)"
        ht['IC_Group']=self.input_ic.icindex
        ht['IC_Alias']="OSA"
        ht['disablePICsIT']="YES"
        ht['GTI_attTolerance_X']="0.05"
        ht['GTI_attTolerance_Z']="0.2"
        ht['GTI_BTI_Dol']=self.input_ic.icroot+"/ic/ibis/lim/isgr_gnrl_bti_0012.fits"
        ht['GTI_BTI_Names']="IBIS_CONFIGURATION IBIS_BOOT ISGRI_RISE_TIME VETO_PROBLEM SOLAR_FLARE BELT_CROSSING"
        ht.run()

        shutil.copy(ht.cwd+"/ibis_gti.fits","./ibis_gti.fits")
        self.output_gti=DataFile("ibis_gti.fits")

# maybe split indeed,but try to show another way
class ibis_dead(DataAnalysis):
    input_scw=ScWData()
    input_ic=ICRoot()
    
    version="v2"
    def main(self):
        # horrible horrible full OSA

        open("scw.list","w").write(self.input_scw.scwid)

        if os.path.exists("obs"):
            os.rename("obs","obs."+str(time.time()))
        
        bin="og_create"
        ogc=heatool(bin)
        ogc['idxSwg']="scw.list"
        ogc['instrument']="IBIS"
        ogc['ogid']="scw_"+self.input_scw.scwid
        ogc['baseDir']="./"
        ogc.run()
        
        scwroot="scw/"+self.input_scw.scwid

        bin="ibis_dead"
        ht=heatool(bin,wd="obs/"+ogc['ogid'].value) 
        ht['swgDOL']=scwroot+"/swg_ibis.fits"
        ht['IC_Group']=self.input_ic.icindex
        ht['IC_Alias']="OSA"
        ht['isgroutDead']="isgri_dead.fits(ISGR-DEAD-SCP.tpl)"
        ht['picsoutDead']="picsit_dead.fits(PICS-DEAD-SCP.tpl)"
        ht['compoutDead']="compton_dead.fits(COMP-DEAD-SCP.tpl)"
        ht['disablePICsIT']="YES"
        ht['disableCompton']="YES"
        ht.run()

        shutil.copy(ht.cwd+"/isgri_dead.fits","./isgri_dead.fits")
        self.output_dead=DataFile("isgri_dead.fits")

class ISGRIEvents(DataAnalysis):
    input_evttag=ibis_isgr_evts_tag()

    version="v2"
    def main(self):
        self.events=self.input_evttag.output_events

class ImageBins(DataAnalysis):
    input_binsname="g25-80"

    def main(self):
        self.bins=[(25,80)]

class ListBins(DataAnalysis):
    input_bins=ImageBins

    def main(self):
        open("f.txt","w").write(str(self.input_bins.bins))

class BinEventsImage(DataAnalysis):
    # how do we guarantee the same ScW is used?..
    input_bins=ImageBins

    input_scw=ScWData()

    input_events=ISGRIEvents()
    input_gti=ibis_gti()
    input_dead=ibis_dead()

    version="v5"

    def main(self):
        # ask stephane why need raw events
        construct_gnrl_scwg_grp(self.input_scw,[\
            self.input_events.events.path, \
            self.input_scw.scwpath+"/isgri_events.fits[3]", \
            self.input_scw.scwpath+"/ibis_hk.fits[IBIS-DPE.-CNV]", \
            self.input_scw.auxadppath+"/time_correlation.fits[AUXL-TCOR-HIS]" \
        ]) # get separately tc etc

        import_attr(self.input_scw.scwpath+"/swg.fits",['OBTSTART','OBTEND'])
        set_attr({'ISDCLEVL':"BIN_I"})

        remove_withtemplate("isgri_detector_shadowgram.fits(ISGR-DETE-SHD-IDX.tpl)")
        remove_withtemplate("isgri_efficiency_shadowgram.fits(ISGR-EFFI-SHD-IDX.tpl)")

        bin="ii_shadow_build"
        ht=heatool(bin)
        ht['outSWGGRP']="og.fits[GROUPING,1,BINTABLE]"
        ht['inDead']=self.input_dead.output_dead.path
        ht['inGTI']=self.input_gti.output_gti.path
        ht['gti_name'] = 'MERGED_ISGRI'
        ht['isgri_e_num'] = len(self.input_bins.bins)
        ht['isgri_e_min'] = " ".join([str(a[0]) for a in self.input_bins.bins])
        ht['isgri_e_max'] = " ".join([str(a[1]) for a in self.input_bins.bins])
        ht['isgri_min_rise'] = 16
        ht['isgri_max_rise'] = 116
        ht['isgri_t_len'] = 10000000
        ht['idxLowThre']=self.input_scw.revdirpath+"/idx/isgri_context_index.fits[1]"
        ht['idxNoisy']=self.input_scw.revdirpath+"/idx/isgri_prp_noise_index.fits[1]"
        ht['outRawShadow']="isgri_detector_shadowgram.fits(ISGR-DETE-SHD-IDX.tpl)"
        ht['outEffShadow']="isgri_efficiency_shadowgram.fits(ISGR-EFFI-SHD-IDX.tpl)"
        ht.run()

        self.shadow_detector=DataFile("isgri_detector_shadowgram.fits")
        self.shadow_efficiency=DataFile("isgri_efficiency_shadowgram.fits")

class BinMapsImage(DataAnalysis):
    input_bins=ImageBins
    input_ic=IBIS_ICRoot
    # and dependency on bkg!

    def main(self):
        #construct_gnrl_scwg_grp(self.input_scw,[\
        #        ])

        construct_empty_shadidx(self.input_bins.bins)

        maps={
                'back':('Bkg','bkg/isgr_back_bkg_0007.fits[1]'),
                'corr':('Corr','mod/isgr_effi_mod_0011.fits[1]'),
                'unif':('Uni','bkg/isgr_unif_bkg_0002.fits[1]')
                }
        
        for k,(k2,m) in maps.items():
            fn="rebinned_"+k+"_ima.fits"

            remove_withtemplate(fn) # again

            bin="ii_map_rebin"
            ht=heatool(bin)
            ht['outSwg']='og.fits[GROUPING,1,BINTABLE]'
            ht['OutType']='BIN_I'
            ht['slope']='-2'
            ht['arfDol']=self.input_ic.ibisicroot+'/mod//isgr_effi_mod_0011.fits[ISGR-ARF.-RSP]'
            ht['inp'+k2+'Dol']=self.input_ic.ibisicroot+"/"+m 
            ht['reb'+k2+'Dol']=fn
            ht.run()

            setattr(self,k+'_ima',DataFile(fn))

class ShadowUBC(DataAnalysis):
    input_scw=ScWData
    input_shadows=BinEventsImage
    input_maps=BinMapsImage

    def main(self):
        construct_gnrl_scwg_grp(self.input_scw,[\
                self.input_shadows.shadow_detector.path,
                self.input_shadows.shadow_efficiency.path,
            ])

        remove_withtemplate("isgri_cor_shad.fits(ISGR-CEXP-SHD-IDX.tpl)")
        
        ht=heatool("ii_shadow_ubc")
        ht['outSWGRP']="og.fits"
        ht['outCorShadow']="isgri_cor_shad.fits(ISGR-CEXP-SHD-IDX.tpl)"
        ht['isgrUnifDol']=self.input_maps.unif_ima.path
        ht['isgrBkgDol']=self.input_maps.back_ima.path
        ht['method_cor']=1
        ht.run()

        self.corshad=DataFile("isgri_cor_shad.fits")

class GRcat(DataAnalysis):
    input="gnrl_ref_cat_33"
    input_ic=ICRoot

    def main(self):
        self.cat=os.environ['REP_BASE_PROD']+"/cat/gnrl_refr_cat_0033_FLAG1.fits[1]"

class GBcat(DataAnalysis):
    input=GRcat
    input_selection="flag5"

    def main(self):
        self.cat=self.input.cat+"[ISGRI_FLAG2==5]"

class ghost_busters(DataAnalysis):
    input=ShadowUBC
    input_ic=IBIS_ICRoot
    input_scw=ScWData
    input_cat=GBcat

    def main(self):
        construct_gnrl_scwg_grp(self.input_scw,[\
                self.input.corshad.path,
                self.input_scw.auxadppath+"/attitude_historic.fits[AUXL-ATTI-HIS,1,BINTABLE]" \
            ])

        import_attr(self.input_scw.scwpath+"/swg.fits",["TSTART","TSTOP"])
        
        ht=heatool("ghost_busters")
        ht['ogDOL']=""
        ht['sourcecat']=self.input_cat.cat
        ht['maskmod']=self.input_ic.ibisicroot+"/mod/isgr_ghos_mod_001.fits[ISGR-GHOS-MOD,1,IMAGE]"
        ht['inDOL']="og.fits"
        ht.run()

        os.rename(self.input.corshad.path,"isgri_cor_shad_gb.fits")

        self.corshad=DataFile("isgri_cor_shad_gb.fits")

class ISGRIRefCat(DataAnalysis):
    input=GRcat
    input_selection="onlyisgri33"

    def main(self):
        self.cat=self.input.cat+"[ISGRI_FLAG==1 || ISGRI_FLAG==2]"

class CatExtract(DataAnalysis):
    input_cat=ISGRIRefCat
    input_scw=ScWData

    def main(self):
        construct_gnrl_scwg_grp(self.input_scw,[\
                ])
        import_attr(self.input_scw.scwpath+"/swg.fits",["RA_SCX","DEC_SCX"])

        remove_withtemplate("isgri_catalog.fits(ISGR-SRCL-CAT.tpl)")

        ht=heatool("cat_extract")
        ht['outGRP']="og.fits[1]"
        ht['outCat']="isgri_catalog.fits(ISGR-SRCL-CAT.tpl)"
        ht['outExt']='ISGR-SRCL-CAT'
        ht['instrument']='ISGRI'
        ht['clobber']='yes'
        ht['refCat']=self.input_cat.cat
        ht.run()

        self.cat=DataFile("isgri_catalog.fits")

class ImagingConfig(DataAnalysis):
    input="default"

    def main(self):
        self.SearchMode=3
        self.ToSearch=5
        self.CleanMode=1
        self.MinCatSouSnr=4
        self.MinNewSouSnr=5
        self.NegModels=0

class ii_skyimage(DataAnalysis):
    input_gb=ghost_busters
    input_maps=BinMapsImage
    input_bins=ImageBins
    input_cat=CatExtract
    input_ic=IBIS_ICRoot
    input_imgconfig=ImagingConfig
    input_scw=ScWData
    input_gti=ibis_gti

    def main(self):
        construct_gnrl_scwg_grp(self.input_scw,[\
                    self.input_gb.corshad.path,
                    self.input_cat.cat.path,
                    self.input_scw.auxadppath+"/time_correlation.fits[AUXL-TCOR-HIS]",
                    self.input_gti.output_gti.path,
                ])
        
        import_attr(self.input_scw.scwpath+"/swg.fits",["OBTSTART","OBTEND","TSTART","TSTOP","SW_TYPE","TELAPSE"])
        set_attr({'ISDCLEVL':"BIN_I"})
        set_attr({'INSTRUME':"IBIS"},"og.fits")

        construct_gnrl_scwg_grp_idx(self.input_scw,[\
                    "og.fits",
                ])
        set_attr({'ISDCLEVL':"BIN_I"},"og_idx.fits")
        
        construct_og(self.input_scw,[\
                    "og_idx.fits",
                ])
        set_attr({'ISDCLEVL':"BIN_I"},"ogg.fits")
        
        remove_withtemplate("isgri_srcl_res.fits(ISGR-SRCL-RES.tpl)")
        remove_withtemplate("isgri_mosa_ima.fits(ISGR-MOSA-IMA-IDX.tpl)")
        remove_withtemplate("isgri_mosa_res.fits(ISGR-MOSA-RES-IDX.tpl)")
        remove_withtemplate("isgri_sky_ima.fits")
        remove_withtemplate("isgri_sky_res.fits")

        ht=heatool("ii_skyimage")
        ht['outOG']="ogg.fits[1]"
        ht['outCat']="isgri_srcl_res.fits(ISGR-SRCL-RES.tpl)"
        ht['mask']=self.input_ic.ibisicroot+"/mod/isgr_mask_mod_0003.fits[ISGR-MASK-MOD,1,IMAGE]"
        ht['deco']=self.input_ic.ibisicroot+"/mod/isgr_deco_mod_0008.fits[ISGR-DECO-MOD,1,IMAGE]"
        ht['tungAtt']=self.input_ic.ibisicroot+"/mod/isgr_attn_mod_0010.fits[ISGR-ATTN-MOD,1,BINTABLE]"
        ht['aluAtt']=self.input_ic.ibisicroot+"/mod/isgr_attn_mod_0011.fits[ISGR-ATTN-MOD,1,BINTABLE]"
        ht['leadAtt']=self.input_ic.ibisicroot+"/mod/isgr_attn_mod_0012.fits[ISGR-ATTN-MOD,1,BINTABLE]"
        ht['covrMod']=self.input_ic.ibisicroot+"/mod/isgr_covr_mod_0002.fits[1]"
        ht['outMosIma']="isgri_mosa_ima.fits(ISGR-MOSA-IMA-IDX.tpl)"
        ht['outMosRes']="isgri_mosa_res.fits(ISGR-MOSA-RES-IDX.tpl)"
        ht['ScwDir'] = './'
        ht['ScwType'] = 'pointing'
        ht['ExtenType'] = 2
        ht['num_band'] = len(self.input_bins.bins)
        ht['E_band_min'] = " ".join([str(a[0]) for a in self.input_bins.bins])
        ht['E_band_max'] = " ".join([str(a[1]) for a in self.input_bins.bins])
        for k in ['SearchMode','ToSearch','CleanMode','MinCatSouSnr','MinNewSouSnr','NegModels','DoPart2']: # dopart2 is flow control, separately
            ht[k]=getattr(self.input_imgconfig,k)
        ht['corrDol'] = self.input_maps.corr_ima.path
        ht.run()

        self.skyima=DataFile("isgri_sky_ima.fits")
        self.skyres=DataFile("isgri_sky_res.fits")


class root(DataAnalysis):
    input=[ibis_gti()]

#
#
#### tools
#
#

def remove_withtemplate(fn):
    s=re.search("(.*?)\((.*?)\)",fn)
    if s is not None:
        try:
            os.remove(s.group(2))
        except OSError:
            pass
        fn=s.group(1)

    try:
        os.remove(fn)
    except OSError:
        pass
    

def construct_gnrl_scwg_grp(scw,children=[],fn="og.fits"):
    dc=heatool("dal_create")
    dc['obj_name']="!"+fn
    dc['template']="GNRL-SCWG-GRP.tpl"
    dc.run()
    
    da=heatool("dal_attr")
    da['indol']=fn
    da['keynam']="REVOL"
    da['action']="WRITE"
    da['type']="DAL_INT"
    da['value_i']=scw.revid
    da.run()
    
    if children!=[]:
        dac=heatool("dal_attach")
        dac['Parent']=fn
        for i,c in enumerate(children):
            dac['Child%i'%(i+1)]=c
            if i>3:
                raise Exception("can not attach more than 4 children to the group!")
        dac.run()

def construct_gnrl_scwg_grp_idx(scw,children=[],fn="og_idx.fits"):
    open("swgs.txt","w").write("\n".join(children))
    dc=heatool("txt2idx")
    dc['element']="swgs.txt"
    dc['index']=fn
    dc['template']="GNRL-SCWG-GRP-IDX.tpl"
    dc.run()

def construct_og(scw,children=[],fn="ogg.fits"):
    dc=heatool("dal_create")
    dc['obj_name']="!"+fn
    dc['template']="GNRL-OBSG-GRP.tpl"
    dc.run()
    
    if children!=[]:
        dac=heatool("dal_attach")
        dac['Parent']=fn
        for i,c in enumerate(children):
            dac['Child%i'%(i+1)]=c
            if i>3:
                raise Exception("can not attach more than 4 children to the group!")
        dac.run()

def import_attr(obj,attr):
    da=heatool("dal_attr_copy")
    da['indol']=obj
    da['outdol']="og.fits"
    da['keylist']=",".join(attr)
    da.run()
    
def set_attr(attrs,fn="og.fits"):

    pt2dt={int:"DAL_INT",str:"DAL_CHAR"}
    pt2k={int:"i",str:"s"}

    for k,v in attrs.items():
        da=heatool("dal_attr")
        da['indol']=fn
        da['keynam']=k
        da['action']="WRITE"
        da['type']=pt2dt[type(v)]
        da['value_'+pt2k[type(v)]]=v
        da.run()
        
def construct_empty_shadidx(bins,fn="og.fits",levl="BIN_I"):
    import pyfits # why now? its expensive and done only if needed

    remove_withtemplate(fn+"(ISGR-DETE-SHD-IDX.tpl)")

    ht=heatool("dal_create")
    ht['obj_name']=fn
    ht['template']="ISGR-DETE-SHD-IDX.tpl"
    ht.run()

    for e1,e2 in bins:
        tshad="shad_%.5lg_%.5lg.fits"%(e1,e2)
        remove_withtemplate(tshad)

        ht=heatool("dal_create")
        ht['obj_name']=tshad
        ht['template']="ISGR-DETE-SHD.tpl"
        ht.run()

        da=heatool("dal_attr")
        da['indol']=ht['obj_name'].value
        da['keynam']="E_MIN"
        da['action']="WRITE"
        da['type']="DAL_DOUBLE"
        da['value_r']=e1
        da.run()

        da=heatool("dal_attr")
        da['indol']=ht['obj_name'].value
        da['keynam']="E_MAX"
        da['action']="WRITE"
        da['type']="DAL_DOUBLE"
        da['value_r']=e2
        da.run()
        
        da=heatool("dal_attr")
        da['indol']=ht['obj_name'].value
        da['keynam']="ISDCLEVL"
        da['action']="WRITE"
        da['type']="DAL_CHAR"
        da['value_s']="BIN_I"
        da.run()

        da=heatool("dal_attach")
        da['Parent']=fn
        da['Child1']=ht['obj_name'].value
        da.run()

    # attaching does not create necessary fields
    
    og=pyfits.open(fn) 
    for i,(e1,e2) in enumerate(bins):
        og[1].data[i]['E_MIN']=e1
        og[1].data[i]['E_MAX']=e2
        og[1].data[i]['ISDCLEVL']=levl
    og.writeto(fn,clobber=True)

