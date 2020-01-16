# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:		validation_tool.py
# Author:	  Tarquini E.
# Created:	 06-12-2019
#-------------------------------------------------------------------------------
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.utils import *
from qgis.core import *
from qgis.gui import *
import os, sys, resources, webbrowser, shutil, collections, processing
from dizio import dizio, dir_list, fls_list, tbl_list, shp_validatore
from validation_tool_dialog import validation_toolDialog


class validation_tool:

    def __init__(self, iface):

        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'validation_tool_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&MS Project Validation Tool')
        self.toolbar = self.iface.addToolBar(u'validation_tool')
        self.toolbar.setObjectName(u'validation_tool')

    def tr(self, message):
        return QCoreApplication.translate('validation_tool', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        self.dlg = validation_toolDialog()
        self.dlg.pushButton_in.clicked.connect(self.select_output_fld_in)

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToDatabaseMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        icon_path = self.plugin_dir + os.sep + 'icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'MS Validation Tool'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        for action in self.actions:
            self.iface.removePluginDatabaseMenu(
                self.tr(u'&MS Validation Tool'),
                action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar


    def check_fld_file(self, e, v, list1, list2, list3):
        if v == 'c':
            var1, var2 = 'la cartella', 'delle cartelle'
        else:
            var1, var2 = 'il file', 'dei files'  
    
        e.write("\n Controllo sulla presenza " + var2 + " di progetto...\n")
        for w in list1:
            if w not in list2:
                e.write("  - Non e' presente " + var1 + " di progetto '" + w + "'\n")
                list3.append(w)
    
        if len(list3) == 0:
            e.write("  Nessun problema riscontrato\n\n")
    
    
    def most_frequent(self, lista): 
        return max(set(lista), key = lista.count)


    def open_pdf(self, pdf_path):
        os.startfile(pdf_path)


    def disableButton(self):
        conteggio = 0
        check_campi = self.dlg.dir_input.text()
        num_lyr = len(QgsMapLayerRegistry.instance().mapLayers())

        i = 0
        for selectLYR in QgsMapLayerRegistry.instance().mapLayers().values():
            i = ++1

        if  num_lyr == 0 and len(check_campi) > 0 and i <= 0:
            self.dlg.button_box.setEnabled(True)
            self.dlg.alert_text.hide()
        else:
            self.dlg.button_box.setEnabled(False)
            self.dlg.alert_text.show()

            
    def select_output_fld_in(self):
        dir_in = QFileDialog.getExistingDirectory(self.dlg, "","", QFileDialog.ShowDirsOnly)
        self.dlg.dir_input.setText(dir_in)


    def check_primitive_crs(self, e, lyr):
        if lyr.name() in ('epuntuali', 'ind_pu', 'geoidr') and str(lyr.wkbType()) not in ('1','4') and lyr.crs().authid().split('EPSG:')[-1] not in ('32633','4258','25832','25833'):
            e.write("    NON POSSIEDE LA PRIMITIVA GEOMETRICA E/O L'EPSG CORRETTO/I!!!\n")
        elif lyr.name() in ('isosub', 'elineari', 'ind_ln') and str(lyr.wkbType()) not in ('2','5') and lyr.crs().authid().split('EPSG:')[-1] not in ('32633','4258','25832','25833'):
            e.write("    NON POSSIEDE LA PRIMITIVA GEOMETRICA E/O L'EPSG CORRETTO/I!!!\n")
        elif lyr.name() in ('geotec', 'forme', 'stab', 'instab') and str(lyr.wkbType()) not in ('3','6') and lyr.crs().authid().split('EPSG:')[-1] not in ('32633','4258','25832','25833'):
            e.write("    NON POSSIEDE LA PRIMITIVA GEOMETRICA E/O L'EPSG CORRETTO/I!!!\n")
        elif lyr.wkbType() == 100:
            e.write("    Tutto OK!\n")
        else:
            e.write("    Possiede primitiva geometrica ed EPSG corretti!\n")


    def out_boundary(self, e, lyr, lyr_com):
        if lyr.wkbType() != 100 and lyr.name() != 'comune_progetto':
            if lyr.featureCount() > 0:
                processing.runalg("qgis:selectbylocation", lyr, lyr_com, u'disjoint', 0, 0)            
                selectFeatures = lyr.selectedFeatures()
                for feat in selectFeatures:
                    e.write("      - La feature con ID " + str(feat.id()) + " ricade al di fuori del perimetro comunale!\n")


    def check_documents(self, nome_cartella, in_dir, nome_dir, lista_miss, nome_fl1, nome_fl2, campo_fl1, campo_fl2, tipo_fl, e):
        if nome_cartella not in lista_miss:
            documenti_dir = in_dir + os.sep + nome_dir + os.sep + nome_cartella
            selectLYR_1 = QgsMapLayerRegistry.instance().mapLayersByName(nome_fl1)[0]
            selectLYR_2 = QgsMapLayerRegistry.instance().mapLayersByName(nome_fl2)[0]
            lista_doc_fld = []
            lista_doc_ind = []

            for x,y,z in os.walk(documenti_dir):
                for q in z:
                    if q.endswith(tipo_fl):
                        lista_doc_fld.append(q)
                    else:
                        e.write("  - ATTENZIONE!!! E' PRESENTE UN FILE CON UN FORMATO DIFFERENTE DAL '" + tipo_fl + "' ALL'INTERNO DELLA CARTELLA '" + nome_cartella + "': '" + q + "'\n")
                        
            flds = selectLYR_1.getFeatures()
            for fld in flds:
                lista_doc_ind.append(fld[campo_fl1])
            flds = selectLYR_2.getFeatures()
            for fld in flds:
                lista_doc_ind.append(fld[campo_fl2])

            for elem_pdf in lista_doc_ind:
                if elem_pdf not in lista_doc_fld:
                    try:
                        e.write("  - ATTENZIONE!!! IL FILE '" + elem_pdf + "' NON E' PRESENTE NELLA CARTELLA '" + nome_cartella + "'\n")
                    except:
                        pass


    def geom_check(self, e, feats):
        if feats.wkbType() != 100 and feats.name() != 'comune_progetto':
            for feature in feats.getFeatures():
                geom = feature.geometry()
                if geom:
                    err = geom.validateGeometry()
                    if err:
                        e.write('	%d individuato errore geometrico (feature %d)\n' % (len(err), feature.id()))


    def identify_gap(self, e, lyr, dir_out):
        if lyr.wkbType() == QGis.WKBPolygon and lyr.name() != 'comune_progetto' or lyr.wkbType()==QGis.WKBMultiPolygon and lyr.name() != 'comune_progetto':
            if lyr.featureCount() > 0:
                e.write("  - Sto eseguendo il controllo relativo alla presenza di gap su '" + lyr.name() + "'...\n")
                output1 = dir_out + os.sep + "elab" + os.sep + lyr.name() + "_diss.shp"
                output2 = dir_out + os.sep + "elab" + os.sep + lyr.name() + "_fill.shp"
                output3 = dir_out + os.sep + "elab" + os.sep + lyr.name() + "_gap.shp"
                processing.runandload("qgis:dissolve", lyr, True, "", output1)
                processing.runandload("qgis:fillholes", output1, 1, output2)
                processing.runandload("qgis:difference", output2, output1, False, output3)
                try:
                    layer_name = QgsMapLayerRegistry.instance().mapLayersByName("Difference")[0]
                except:
                    layer_name = QgsMapLayerRegistry.instance().mapLayersByName("Differenza")[0]
                layer_name.setLayerName(lyr.name() + "_gap")
                layer_name.startEditing()
                for fc in layer_name.getFeatures(QgsFeatureRequest().setFilterExpression("$geometry IS NULL").setSubsetOfAttributes([]).setFlags(QgsFeatureRequest.NoGeometry)):
                    layer_name.deleteFeature(fc.id())
                layer_name.commitChanges()
                e.write("     Eseguito! Il file contenente i gap del layer '" + lyr.name() + "' e' stato salvato nella directory '\\elab\\" + lyr.name() + "_gap.shp'\n\n")


    def topology_check(self, directory, lyr1, lyr2, campo1, campo2, nome1, nome2, nome3, e):
        processing.runandload("saga:polygonselfintersection", lyr1, campo1, directory + os.sep + nome1 + ".shp")
        self.elab_self_intersect(nome1, campo1)
        self.remove_record(nome1)
        e.write("     Eseguito! Il file contenente le aree di self-intersection del layer '" + lyr1 + "' e' stato salvato nella directory '\\elab\\" + nome1 + ".shp'\n")
        processing.runandload("saga:polygonselfintersection", lyr2, campo2, directory + os.sep + nome2 + ".shp")
        self.elab_self_intersect(nome2, campo2)
        self.remove_record(nome2)
        e.write("     Eseguito! Il file contenente le aree di self-intersection del layer '" + lyr2 + "' e' stato salvato nella directory '\\elab\\" + nome2 + ".shp'\n")
        processing.runandload("saga:intersect", lyr1, lyr2, True, directory + os.sep + nome3 + ".shp")
        self.elab_intersect(nome3)
        self.remove_record(nome3)
        e.write("     Eseguito! Il file contenente le aree di intersezione tra '" + lyr1 + "' e '" + lyr2 + "' e' stato salvato nella directory '\\elab\\" + nome3 + ".shp'\n\n")


    def elab_intersect(self, nome_file_inters):
        layer_name = QgsMapLayerRegistry.instance().mapLayersByName("Intersection")[0]
        layer_name.setLayerName(nome_file_inters)
        field_ids = []

        fieldnames = set(['ID_z', 'ID_i'])
        for field in layer_name.fields():
            if field.name() not in fieldnames:
                field_ids.append(layer_name.fieldNameIndex(field.name()))
        layer_name.dataProvider().deleteAttributes(field_ids)
        layer_name.updateFields()


    def elab_self_intersect(self, nome_file_inters, nome_campo):
        layer_name = QgsMapLayerRegistry.instance().mapLayersByName("Intersection")[0]
        layer_name.setLayerName(nome_file_inters)
        layer_name.startEditing()
        for fc in layer_name.getFeatures(QgsFeatureRequest().setFilterExpression(nome_campo + '!= 0').setSubsetOfAttributes([]).setFlags(QgsFeatureRequest.NoGeometry)):
            layer_name.deleteFeature(fc.id())
        layer_name.commitChanges()

        field_ids = []
        fieldnames = set(['ID'])
        for field in layer_name.fields():
            if field.name() not in fieldnames:
                field_ids.append(layer_name.fieldNameIndex(field.name()))
        layer_name.dataProvider().deleteAttributes(field_ids)
        layer_name.updateFields()


    def remove_record(self, lyr_name):
        layer_name = QgsMapLayerRegistry.instance().mapLayersByName(lyr_name)[0]
        layer_name.startEditing()
        for elem in layer_name.getFeatures():
            try:
                if elem.geometry().area() < 1:				
                    layer_name.deleteFeature(elem.id())
            except AttributeError:
                layer_name.deleteFeature(elem.id())
        layer_name.commitChanges()


    def run(self):
        self.dlg.igag.setPixmap(QPixmap(self.plugin_dir + os.sep + "img" + os.sep + 'logo-igag.png'))
        self.dlg.cnr.setPixmap(QPixmap(self.plugin_dir + os.sep + "img" + os.sep + 'logo-cnr.png'))
        self.dlg.labgis.setPixmap(QPixmap(self.plugin_dir + os.sep + "img" + os.sep + 'logo-labgis.png'))
        self.dlg.pushButton_ita.clicked.connect(lambda: self.open_pdf(self.plugin_dir + os.sep + "manuale.pdf"))
        self.dlg.dir_input.clear()
        self.dlg.alert_text.hide()
        self.dlg.button_box.setEnabled(False)
        self.dlg.dir_input.textChanged.connect(self.disableButton)

        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            in_dir = self.dlg.dir_input.text()
            if os.path.isdir(in_dir):
                folder_list = []
                file_list = []
                missing_fold_list = []
                missing_file_list = []

                crs = QgsCoordinateReferenceSystem(32633)
                iface.mapCanvas().mapRenderer().setDestinationCrs(crs)

                ## creation log file and 'elab' folder
                logfile = in_dir + os.sep + str(time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime())) + "_validation_log.txt"
                e = open(logfile,'a')
                e.write("REPORT DI VALIDAZIONE:" +"\n----------------------\n\n")

                if not os.path.exists(in_dir + os.sep + 'elab'):
                    os.makedirs(in_dir + os.sep + 'elab')
                else:
                    shutil.rmtree(in_dir + os.sep + 'elab')
                    os.makedirs(in_dir + os.sep + 'elab')

                ## check project folders/files
                for x,y,z in os.walk(in_dir):
                    for p in y:
                        folder_list.append(p)
                    for q in z:
                        file_list.append(q)
                
                e.write("1. Controllo struttura del progetto:")
                self.check_fld_file(e, "c", dir_list, folder_list, missing_fold_list)
                self.check_fld_file(e, "f", fls_list, file_list, missing_file_list)

                ## municipality identification and layer loading
                iface.addVectorLayer(self.plugin_dir + os.sep + "data" + os.sep + "comuni.shp", "", "ogr")

                for drs, tbls in dizio.iteritems():
                    if drs == "CdI_Tabelle":
                        pass
                    else:
                        for tbl in tbls:
                            lyr_dir = in_dir + os.sep + drs + os.sep + tbl['table'] + ".shp"
                            if os.path.isfile(lyr_dir):
                                iface.addVectorLayer(lyr_dir,'', "ogr")
            
                if 'Ind_pu.shp' not in missing_file_list:
                    sourceLYR = QgsMapLayerRegistry.instance().mapLayersByName("Ind_pu")[0]
                    list_code = []
                    for feat in sourceLYR.getFeatures():
                        attrs = feat.attributes()
                        list_code.append(attrs[0][:6])
                    
                    if len(list_code) > 0:
                        cod_istat = self.most_frequent(list_code)
                        destLYR = QgsMapLayerRegistry.instance().mapLayersByName("comuni")[0]
                        selection = destLYR.getFeatures(QgsFeatureRequest().setFilterExpression (u""""cod_istat" = '""" + cod_istat + """'"""))
                        destLYR.setSelectedFeatures([k.id() for k in selection])
                        selected_features = destLYR.selectedFeatures()
                        
                        for feat in selected_features:
                            attrs = feat.attributes()
                            codice_istat = attrs[5]
                            nome = attrs[4]
                            regione = attrs[7]
                            provincia = attrs[6]
                        
                        e.write('\n Comune di %s in provincia di %s, regione %s (codice ISTAT %s)\n\n' %(nome,provincia,regione,codice_istat))

                        QgsVectorFileWriter.writeAsVectorFormat(destLYR, in_dir + os.sep + 'elab' + os.sep + 'comune_progetto.shp', 'utf-8', destLYR.crs(), 'ESRI Shapefile', True)
                        iface.addVectorLayer(in_dir + os.sep + 'elab' + os.sep + "comune_progetto.shp",'', "ogr")
                        destLYR.removeSelection() 
                        QgsMapLayerRegistry.instance().removeMapLayers([destLYR.id()]) 

                if 'CdI_Tabelle.sqlite' not in missing_file_list:
                    percorso = QgsDataSourceURI()
                    percorso.setDatabase(in_dir + os.sep + "Indagini" + os.sep + "CdI_Tabelle.sqlite")

                    for tabella in tbl_list:
                        try:
                            percorso.setDataSource("", tabella, "")
                            iface.addVectorLayer(percorso.uri(), tabella, 'spatialite')
                        except:
                            pass

                e.write("\n2. Validazione attributi e valori:\n")
                ## fields and records table check
                e.write(" Controllo dello schema delle tabelle...\n")
                for drs, tbls in dizio.iteritems():
                    for tbl in tbls:
                        try:
                            e.write('  ------------\n  + ' + drs.upper() + '  -  ' + tbl['table'].upper() + '\n')
                            dizio_layer = {}
                            shp_layer = {}
                            for campo in tbl['fields']:
                                dizio_layer.update({campo['field']:campo['type']})
                            selectLYR = QgsMapLayerRegistry.instance().mapLayersByName(tbl['table'])[0]
                            flds = selectLYR.fields()
                            for fld in flds:
                                shp_layer.update({fld.name():fld.typeName()})
                                
                            for chiave_dizio, value_dizio in dizio_layer.iteritems():
                                if chiave_dizio in shp_layer.keys():
                                    if shp_layer[chiave_dizio] in value_dizio:
                                        e.write("   - '" + chiave_dizio + "' e' presente - DataType rispettato: " + shp_layer[chiave_dizio] + '\n')
                                    else:
                                        e.write("   - '" + chiave_dizio + "' e' presente ma il DataType NON E' RISPETTATO!!! Dovrebbe essere: " + str(value_dizio).replace('[','').replace(']','') + '\n')
                                elif chiave_dizio not in shp_layer.keys():
                                    e.write("   - '" + chiave_dizio + "' NON E' PRESENTE!!!\n")
                        except:
                            e.write("   - '" + tbl['table'].upper() + "' NON ESISTE!\n")
                            
                ## number of records in the tables
                e.write("\n Conteggio dei record delle tabelle/feature class...\n")          
                for drs, tbls in dizio.iteritems():
                    for tbl in tbls:
                        try:
                            selectLYR = QgsMapLayerRegistry.instance().mapLayersByName(tbl['table'])[0]
                            conteggio = selectLYR.featureCount()
                            if conteggio <= 0:
                                e.write("  - ATTENZIONE!!! IL NUMERO DEI RECORD DELLA TABELLA/FEATURE CLASS '" + tbl['table'] + "' E' PARI A ZERO\n")
                            elif conteggio > 0:
                                e.write("  - Il numero di record della tabella/feature class '" + tbl['table'] + "' e': " + str(conteggio) + "\n")

                            if 'Ind_pu.shp' not in missing_file_list and 'Ind_ln.shp' not in missing_file_list and 'CdI_Tabelle.sqlite' not in missing_file_list:
                                if tbl['table'] in ('Ind_pu', 'Ind_ln', 'sito_puntuale', 'sito_lineare'):
                                    if selectLYR.name() == 'Ind_pu':
                                        count_ind_pu = conteggio
                                        lista_ind_pu =[]
                                        flds = selectLYR.getFeatures()
                                        for fld in flds:
                                            lista_ind_pu.append(fld['ID_SPU'])
                                    elif selectLYR.name() == 'Ind_ln':
                                        count_ind_ln = conteggio
                                        lista_ind_ln =[]
                                        flds = selectLYR.getFeatures()
                                        for fld in flds:
                                            lista_ind_ln.append(fld['ID_SLN'])
                                    if selectLYR.name() == 'sito_puntuale':
                                        count_sito_puntuale = conteggio
                                        lista_sito_puntuale =[]
                                        set_pro_com_pu = set([])
                                        flds = selectLYR.getFeatures()
                                        for fld in flds:
                                            lista_sito_puntuale.append(fld['ID_SPU'])
                                            cod_pro_com_pu = fld['ubicazione_prov'] + fld['ubicazione_com']
                                            set_pro_com_pu.add(cod_pro_com_pu)
                                    elif selectLYR.name() == 'sito_lineare':
                                        count_sito_lineare = conteggio
                                        lista_sito_lineare =[]
                                        set_pro_com_ln = set([])
                                        flds = selectLYR.getFeatures()
                                        for fld in flds:
                                            lista_sito_lineare.append(fld['ID_SLN'])
                                            cod_pro_com_ln = fld['ubicazione_prov'] + fld['ubicazione_com']
                                            set_pro_com_ln.add(cod_pro_com_ln)  
                        except:
                            pass     
                                              
                if 'Ind_ln.shp' not in missing_file_list and 'Ind_pu.shp' not in missing_file_list and 'CdI_Tabelle.sqlite' not in missing_file_list:
                    e.write("\n Controllo dei Siti d'indagine e dei documenti PDF correlati...\n")
                    if count_ind_pu != count_sito_puntuale:
                        e.write("  - ATTENZIONE!!! IL NUMERO DI RECORD DELLA TABELLA 'ind_pu' E' DIVERSO DAL NUMERO DI RECORD DELLA FEATURE CLASS 'sito_puntuale'\n")
                    if collections.Counter(lista_ind_pu) != collections.Counter(lista_sito_puntuale):
                        e.write("  - ATTENZIONE!!! ESISTONO DEI VALORI NEL CAMPO 'ID_SPU' CHE NON COINCIDONO TRA 'IND_PU' E 'SITO_PUNTUALE'!!!\n")                
                    if count_ind_ln != count_sito_lineare:
                        e.write("  - ATTENZIONE!!! IL NUMERO DI RECORD DELLA TABELLA 'ind_ln' E' DIVERSO DAL NUMERO DI RECORD DELLA FEATURE CLASS 'sito_lineare'\n")                    
                    if collections.Counter(lista_ind_ln) != collections.Counter(lista_sito_lineare):
                        e.write("  - ATTENZIONE!!! ESISTONO DEI VALORI NEL CAMPO 'ID_SLN' CHE NON COINCIDONO TRA 'IND_LN' E 'SITO_LINEARE'!!!\n")
                    for codice in set_pro_com_pu:
                        if str(codice) != str(codice_istat):
                            e.write("  - ATTENZIONE!!! E' PRESENTE UNA FEATURE IN 'sito_puntuale' CON VALORI IN 'ubicazione_prov' E 'ubicazione_com' DIVERSI DA QUELLI DEL COMUNE DI PROGETTO\n")
                    for codice in set_pro_com_ln:
                        if str(codice) != str(codice_istat):
                            e.write("  - ATTENZIONE!!! E' PRESENTE UNA FEATURE IN 'sito_lineare' CON VALORI IN 'ubicazione_prov' E 'ubicazione_com' DIVERSI DA QUELLI DEL COMUNE DI PROGETTO\n")

                self.check_documents("Documenti",in_dir, "Indagini", "missing_file_list", "indagini_puntuali", "indagini_lineari", "doc_ind", "doc_ind", ".pdf", e)
                self.check_documents("Spettri",in_dir, "MS23", "missing_file_list", "instab", "stab", "SPETTRI", "SPETTRI", ".txt", e)

                ## check of domains and uniqueness
                e.write("\n Rispetto dei domini e delle restrizioni di tipo 'unique'...\n")                  
                for drs, tbls in dizio.iteritems():
                    for tbl in tbls:
                        for campi in tbl['fields']:
                            if campi['isuq'] is True:
                                try:
                                    list_unique = []
                                    selectLYR = QgsMapLayerRegistry.instance().mapLayersByName(tbl['table'])[0]
                                    features = selectLYR.getFeatures()
                                    for f in features:
                                        list_unique.append(f[campi['field']])
                                    e.write("  - Nella tabella '" + tbl['table'] + "' nel campo '" + campi['field'] + "' i seguenti valori si ripetono: " + str([item for item, count in collections.Counter(a).items() if count > 1]).replace('[','').replace(']','') + "\n")
                                except:
                                    pass
                            if campi['listvalues'] is not False:
                                try:
                                    list_domini = campi['listvalues']
                                    if campi['field'] not in ('Gen','Stato'):
                                        selectLYR = QgsMapLayerRegistry.instance().mapLayersByName(tbl['table'])[0]
                                        features = selectLYR.getFeatures()
                                        for f in features:
                                            if f[campi['field']] not in list_domini:
                                                e.write("  - Nella tabella '" + tbl['table'] + "' nel campo '" + campi['field'] + "' il seguente valore non rispetta il dominio: " + str(f[campi['field']]) + " (ID: " + str(f.id()) +")\n")
                                except:
                                    pass

                ## further checks (geotec, geoidr, stab, instab)
                for drs, tbls in dizio.iteritems():
                    for tbl in tbls:
                        #try:
                        if tbl['table'] == 'geotec' and 'Geotec.shp' not in missing_file_list:
                            selectLYR = QgsMapLayerRegistry.instance().mapLayersByName(tbl['table'])[0]
                            features = selectLYR.getFeatures()
                            for f in features:
                                if f['Tipo_gt'] in ['RI', 'GW', 'GP', 'GM', 'GC', 'SW', 'SP', 'SM', 'SC', 'OL', 'OH', 'MH', 'ML', 'CL', 'CH', 'PT']:
                                    if f['Stato'] not in tbl['fields'][2]['listvalues']:
                                        e.write("  - Nella tabella '" + tbl['table'] + "' nel campo 'Stato' il seguente valore non rispetta il dominio: " + str(f['Stato']) + " (ID: " + str(f.id()) +")\n")  
                                    if f['Gen'] not in tbl['fields'][3]['listvalues']:
                                        e.write("  - Nella tabella '" + tbl['table'] + "' nel campo 'Gen' il seguente valore non rispetta il dominio: " + str(f['Gen']) + " (ID: " + str(f.id()) +")\n")   
                                elif f['Tipo_gt'] in ['LP', 'GR', 'CO', 'AL', 'LPS', 'GRS', 'COS', 'ALS', 'SFLP', 'SFGR', 'SFCO', 'SFAL', 'SFLPS', 'SFGRS', 'SFCOS', 'SFALS', 'CVT']:
                                    if f['Stato'] not in ['',None]:
                                        e.write("  - Nella tabella '" + tbl['table'] + "' nel campo 'Stato' il seguente valore non rispetta la condizione 'deve essere Null': " + str(f['Stato']) + " (ID: " + str(f.id()) +")\n")  
                                    if f['Gen'] not in ['',None]:
                                        e.write("  - Nella tabella '" + tbl['table'] + "' nel campo 'Gen' il seguente valore non rispetta la condizione 'deve essere Null': " + str(f['Gen']) + " (ID: " + str(f.id()) +")\n")  
                        elif tbl['table'] == 'geoidr' and 'Geoidr.shp' not in missing_file_list:
                            selectLYR = QgsMapLayerRegistry.instance().mapLayersByName(tbl['table'])[0]
                            features = selectLYR.getFeatures()
                            for f in features:
                                if f['Tipo_gi'] == '11':
                                    if f['Valore'] < 0 or f['Valore'] > 360: 
                                        e.write("  - Nella tabella '" + tbl['table'] + "' nel campo 'Valore' il seguente valore non rispetta la condizione 'compreso tra 0 e 360': " + str(f['Valore']) + " (ID: " + str(f.id()) +")\n") 
                                    if f['Valore2'] < 0 or f['Valore2'] > 90: 
                                        e.write("  - Nella tabella '" + tbl['table'] + "' nel campo 'Valore2' il seguente valore non rispetta la condizione 'compreso tra 0 e 90': " + str(f['Valore2']) + " (ID: " + str(f.id()) +")\n") 
                                elif f['Tipo_gi'] in ['21','22','31']:
                                    if f['Valore2'] not in [0,None]: 
                                        e.write("  - Nella tabella '" + tbl['table'] + "' nel campo 'Valore2' il seguente valore non rispetta la condizione 'deve essere 0 o Null': " + str(f['Valore2']) + " (ID: " + str(f.id()) +")\n")
                        elif tbl['table'] == 'parametri_puntuali' and 'CdI_Tabelle.sqlite' not in missing_file_list:
                            selectLYR = QgsMapLayerRegistry.instance().mapLayersByName(tbl['table'])[0]
                            features = selectLYR.getFeatures()
                            for f in features:
                                if f['tipo_parpu'] == 'L':
                                    if f['valore'] not in ('RI', 'GW', 'GP', 'GM', 'GC', 'SW', 'SP', 'SM', 'SC', 'OL', 'OH', 'MH', 'ML', 'CL', 'CH', 'PT', 'LP', 'GR', 'CO', 'AL', 'LPS', 'GRS', 'COS', 'ALS', 'SFLP', 'SFGR', 'SFCO', 'SFAL', 'SFLPS', 'SFGRS', 'SFCOS', 'SFALS', 'CVT'):
                                        e.write("  - Nella tabella '" + tbl['table'] + "' nel campo 'Valore' non e' presente un codice identificativo del litotipo (ID: " + str(f.id()) +")\n")
                        #except:
                            #pass 

                for selectLYR in QgsMapLayerRegistry.instance().mapLayers().values():
                    if selectLYR.name() in ('stab','instab'):
                        origine = selectLYR.source().split('MS')[-1]
                        features = selectLYR.getFeatures()
                        if origine.startswith('1'):
                            for f in features:
                                try:
                                    if f['LIVELLO'] != 1:
                                        e.write("  - Nella tabella '" + selectLYR.name() + "' (nella cartella 'MS1') nel campo 'LIVELLO' il seguente valore e' diverso da 1: " + str(f['LIVELLO']) + " (ID: " + str(f.id()) +")\n")
                                except:
                                    pass
                        elif origine.startswith('23'):
                            for f in features:
                                try:
                                    if f['LIVELLO'] not in (2,3):
                                        e.write("  - Nella tabella '" + selectLYR.name() + "' (nella cartella 'MS23') nel campo 'LIVELLO' il seguente valore e' diverso da 2 o 3: " + str(f['LIVELLO']) + " (ID: " + str(f.id()) +")\n")
                                except:
                                    pass

                e.write("  Analisi terminata!\n")

                e.write("\n\n3. Validazione geometrica:\n")
                ## geometric primitive identification and CRS 
                if QgsMapLayerRegistry.instance().mapLayersByName('comune_progetto') == []:
                    pass
                else:
                    lyr_com = QgsMapLayerRegistry.instance().mapLayersByName('comune_progetto')[0]
                    layers = QgsMapLayerRegistry.instance().mapLayers().values()
                    for lyr in layers:
                        if lyr.wkbType() == QGis.WKBPoint:
                            tipo = " possiede una geometria puntuale (" + lyr.crs().authid() + ")\n"                            
                        elif lyr.wkbType() == QGis.WKBLineString:
                            tipo = " possiede una geometria lineare (" + lyr.crs().authid() + ")\n"
                        elif lyr.wkbType() == QGis.WKBPolygon:
                            tipo = " possiede una geometria poligonale (" + lyr.crs().authid() + ")\n"
                        elif lyr.wkbType() == QGis.WKBMultiPoint:
                            tipo = " possiede una geometria puntuale (" + lyr.crs().authid() + ")\n"
                        elif lyr.wkbType() == QGis.WKBMultiLineString:
                            tipo = " possiede una geometria lineare (" + lyr.crs().authid() + ")\n"
                        elif lyr.wkbType()==QGis.WKBMultiPolygon:
                            tipo = " possiede una geometria multi-poligonale (" + lyr.crs().authid() + ")\n"
                        elif lyr.wkbType() == 100:
                            tipo = " non possiede una geometria in quanto e' una tabella\n"
                        e.write("  - Il layer " + lyr.name() + tipo)
                        self.geom_check(e, lyr)
                        self.check_primitive_crs(e, lyr)
                        self.out_boundary(e, lyr, lyr_com)

                e.write("\n\n4. Validazione topologica:\n") 

                intersezioni_geotec = True
                intersezioni_ms1 = True
                intersezioni_ms23 = True

                if "geotec" in missing_file_list:
                    intersezioni_geotec = False
                if "stab" in missing_file_list or "instab" in missing_file_list:
                    intersezioni_ms1 = False
                if "stab" in missing_file_list or "instab" in missing_file_list:
                    intersezioni_ms23 = False

                for selectLYR in QgsMapLayerRegistry.instance().mapLayers().values():
                    if selectLYR.name() in ('stab','instab'):
                        origine = selectLYR.source().split('MS')[-1]
                        features = selectLYR.getFeatures()
                        if origine.startswith('1'):
                            if selectLYR.name() == 'stab':
                                selectLYR.setLayerName("stab1")
                            elif selectLYR.name() == 'instab': 
                                selectLYR.setLayerName("instab1")
                        elif origine.startswith('23'):
                            if selectLYR.name() == 'stab':
                                selectLYR.setLayerName("stab23")
                            elif selectLYR.name() == 'instab': 
                                selectLYR.setLayerName("instab23")

                ## gap check
                layers = QgsMapLayerRegistry.instance().mapLayers().values()
                for lyr in layers:         
                    self.identify_gap(e, lyr, in_dir)                                

                ## intersection and auto-intersection check
                e.write("  - Sto eseguendo il controllo topologico su 'geotec'...\n")
                if intersezioni_geotec is True:
                    processing.runandload("saga:polygonselfintersection", "geotec", "ID_gt", in_dir + os.sep + "elab" + os.sep + "geotec_self_inters.shp")
                    self.elab_self_intersect("geotec_self_inters", "ID_gt")
                    self.remove_record("geotec_self_inters")
                    e.write("     Eseguito! Il file contenente le aree di self-intersection del layer 'geotec' e' stato salvato nella directory '\\elab\\geotec_self_inters.shp'\n\n")
                else:
                    e.write("     Il controllo topologico non puo' essere eseguito in quanto manca il layer 'geotec'!\n\n")

                e.write("  - Sto eseguendo il controllo topologico su 'stab' e 'instab' livello 1...\n")
                if intersezioni_ms1 is True:
                    self.topology_check(in_dir + os.sep + "elab", "stab1", "instab1", "ID_z", "ID_i", "stab_1_self_inters", "instab_1_self_inters", "ms1_inters_stab_instab", e)
                else:
                    e.write("     Il controllo topologico non puo' essere eseguito in quanto manca/ano il/i layer 'stab' e/o 'instab'!\n\n")

                e.write("  - Sto eseguendo il controllo topologico su 'stab' e 'instab' livello 2-3...\n")
                if intersezioni_ms23 is True:
                    self.topology_check(in_dir + os.sep + "elab", "stab23", "instab23", "ID_z", "ID_i", "stab_23_self_inters", "instab_23_self_inters", "ms23_inters_stab_instab", e)
                else:
                    e.write("     Il controllo topologico non puo' essere eseguito in quanto manca/ano il/i layer 'stab' e/o 'instab'!\n\n")

                e.write("  Analisi terminata!\n")
                QMessageBox.information(None, u'INFORMATION!', u"Validation summary report was saved in the project folder!")

                for layer in iface.mapCanvas().layers():
                    if layer.name() in shp_validatore:
                        feats_count = layer.featureCount()
                        if feats_count == 0:
                            QgsMapLayerRegistry.instance().removeMapLayer(layer)

                root = QgsProject.instance().layerTreeRoot()
                root.addGroup("Validazione")
                toc = iface.legendInterface()
                groups = toc.groups()
                groupIndex = groups.index("Validazione")
                canvas = iface.mapCanvas()
                layers = canvas.layers()
                for i in layers:
                    if i.name() in shp_validatore:
                        alayer = i
                        toc.moveLayer(i, groupIndex)
                    canvas.refresh()

                layers = QgsMapLayerRegistry.instance().mapLayers().values()
                for lyr in layers:
                    if lyr.name() in ("Dissolved", "Results", "Dissolti"):
                        QgsMapLayerRegistry.instance().removeMapLayer(lyr)

                e.close()

            else:
                QMessageBox.warning(iface.mainWindow(), u'WARNING!', u"The selected directory does not exist!")