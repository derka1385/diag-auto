"use client";

import {FormEvent,useEffect,useMemo,useState} from "react";
import {Inter} from "next/font/google";
import {useRouter} from "next/navigation";
import {api} from "@/services/api";
import type {Vehicle,VehicleResolveResult} from "@/types";

const inter=Inter({subsets:["latin"],weight:["400","500","600","700","800"]});
const mono={fontFamily:"ui-monospace, 'SF Mono', Menlo, monospace"} as const;
const labels=["Véhicule","Défauts","Preuves","Validation"];
type Measurement={name:string;value:string;unit:string;conditions:string};
type ImageDraft={file:File;preview:string;category:string;description:string};
type ManualVehicle={make:string;model:string;generation:string;model_year:string;fuel_type:string;engine_displacement_cc:string;engine_power_hp:string;engine_code:string;transmission_type:string;transmission_code:string;transmission_gears:string;drivetrain:string;tecdoc_k_type:string;cnit:string};

export default function NewDiagnostic(){
 const router=useRouter();
 const [step,setStep]=useState(1);const [vehicles,setVehicles]=useState<Vehicle[]>([]);const [vehicleId,setVehicleId]=useState("");
 const [registration,setRegistration]=useState("");const [country,setCountry]=useState("FR");const [lookup,setLookup]=useState<VehicleResolveResult|null>(null);const [candidateId,setCandidateId]=useState("");
 const [identifierMode,setIdentifierMode]=useState<"registration"|"vin">("registration");const [vin,setVin]=useState("");const [manualOpen,setManualOpen]=useState(false);const [manual,setManual]=useState<ManualVehicle>({make:"",model:"",generation:"",model_year:"",fuel_type:"diesel",engine_displacement_cc:"",engine_power_hp:"",engine_code:"",transmission_type:"manual",transmission_code:"",transmission_gears:"",drivetrain:"fwd",tecdoc_k_type:"",cnit:""});
 const [mileage,setMileage]=useState("84200");const [symptoms,setSymptoms]=useState("");const [circumstances,setCircumstances]=useState("");
 const [codes,setCodes]=useState("P1351");const [ecu,setEcu]=useState("ECU moteur");const [status,setStatus]=useState("active");
 const [measurements,setMeasurements]=useState<Measurement[]>([]);const [measure,setMeasure]=useState<Measurement>({name:"",value:"",unit:"",conditions:""});
 const [images,setImages]=useState<ImageDraft[]>([]);const [uploadProgress,setUploadProgress]=useState(0);
 const [busy,setBusy]=useState(false);const [error,setError]=useState("");
 const parsedCodes=useMemo(()=>codes.split(/[ ,;\n]+/).map(x=>x.trim().toUpperCase()).filter(Boolean),[codes]);
 const vehicle=vehicles.find(x=>x.id===vehicleId);
 useEffect(()=>{api.vehicles().then(setVehicles).catch(e=>setError(e.message))},[]);

 async function identify(e:FormEvent){e.preventDefault();setBusy(true);setError("");setVehicleId("");setLookup(null);try{const body=identifierMode==="registration"?{registration,country_code:country}:{vin,country_code:country};const result=await api.resolveVehicle(body);const candidate=result.candidates?.[0];setLookup(result);setCandidateId(candidate?.id??"");const motorMissing=!candidate?.engine_code;setManualOpen(motorMissing);if(candidate&&motorMissing)setManual(current=>({...current,make:candidate.make??"",model:candidate.model??"",generation:candidate.generation??"",model_year:candidate.model_year?String(candidate.model_year):"",fuel_type:candidate.fuel_type??current.fuel_type,engine_displacement_cc:candidate.engine_displacement_cc?String(candidate.engine_displacement_cc):"",engine_power_hp:candidate.engine_power_hp?String(candidate.engine_power_hp):"",transmission_type:candidate.transmission_type??current.transmission_type,transmission_code:candidate.transmission_code??"",transmission_gears:candidate.transmission_gears?String(candidate.transmission_gears):""}));if(motorMissing)setError("Le fournisseur n’a pas identifié précisément le moteur. Vérifiez et saisissez le code moteur avant de confirmer.")}catch(e){setError(e instanceof Error?e.message:"Identification impossible")}finally{setBusy(false)}}
 async function confirmVehicle(){if(!lookup?.resolution_id||(!candidateId&&!manualOpen))return;if(lookup.status==="confirmed"&&lookup.vehicle_id&&!manualOpen){setBusy(true);setError("");try{const next=await api.vehicles();setVehicles(next);setVehicleId(lookup.vehicle_id);setLookup(null);setStep(2)}catch(e){setError(e instanceof Error?e.message:"Confirmation impossible")}finally{setBusy(false)}return}const corrections=manualOpen?Object.fromEntries(Object.entries(manual).filter(([,value])=>value!=="").map(([key,value])=>[key,["model_year","engine_displacement_cc","engine_power_hp","transmission_gears"].includes(key)?Number(value):value])):{};if(manualOpen&&(!manual.make||!manual.model||!manual.engine_code))return setError("En mode manuel, marque, modèle et code moteur sont obligatoires.");setBusy(true);setError("");try{const data=await api.confirmResolution(lookup.resolution_id,{candidate_id:manualOpen?null:candidateId,corrections,configuration_unknown:false,registration:registration||null,registration_country:country,technician_note:manualOpen?"Identité technique confirmée manuellement par le garagiste.":null});const next=await api.vehicles();setVehicles(next);setVehicleId(data.vehicle.id);setLookup(null);setStep(2)}catch(e){setError(e instanceof Error?e.message:"Confirmation impossible")}finally{setBusy(false)}}
 function advance(){setError("");if(step===1&&!vehicleId)return setError("Sélectionnez ou identifiez un véhicule.");if(step===2){if(!parsedCodes.length||parsedCodes.some(x=>!/[PBCU][0-9A-F]{4}/.test(x)))return setError("Saisissez des codes OBD valides, par exemple P1351.")}setStep(x=>Math.min(4,x+1))}
 function goToStep(target:number){if(target<step){setError("");setStep(target)}}
 function addMeasurement(){if(!measure.name.trim()||!measure.value.trim())return setError("Indiquez le nom et la valeur de la mesure.");setMeasurements(x=>[...x,measure]);setMeasure({name:"",value:"",unit:"",conditions:""});setError("")}
 function addImages(list:FileList|File[]){const accepted=Array.from(list).filter(file=>["image/jpeg","image/png","image/webp"].includes(file.type));setImages(current=>[...current,...accepted.slice(0,8-current.length).map(file=>({file,preview:URL.createObjectURL(file),category:"engine_bay",description:""}))]);if(accepted.length!==Array.from(list).length)setError("Certains fichiers ont été ignorés : utilisez JPEG, PNG ou WebP.")}
 function removeImage(index:number){setImages(current=>{URL.revokeObjectURL(current[index].preview);return current.filter((_,i)=>i!==index)})}
 async function submit(){if(!vehicleId)return;setBusy(true);setError("");setUploadProgress(0);try{const created=await api.createDiagnostic({vehicle_id:vehicleId,mileage:mileage?Number(mileage):null,symptoms,circumstances});await api.addFaultCodes(created.id,{fault_codes:parsedCodes.map(code=>({code,ecu:ecu||null,status,freeze_frame:{}}))});for(const item of measurements){const numeric=Number(item.value);await api.addMeasurement(created.id,{name:item.name,value:Number.isFinite(numeric)&&item.value.trim()!==""?numeric:item.value,unit:item.unit||null,conditions:item.conditions,source:"manual"})}for(let i=0;i<images.length;i++){const item=images[i];const data=new FormData();data.append("files",item.file);data.append("category",item.category);data.append("description",item.description);await api.uploadImages(created.id,data);setUploadProgress(Math.round(((i+1)/images.length)*100))}await api.analyzeDiagnostic(created.id);router.push(`/diagnostics/ai/${created.id}`)}catch(e){setError(e instanceof Error?e.message:"Analyse impossible");setBusy(false)}}

 const accent="#33495C";
 const border="rgba(16,22,28,0.09)";
 const borderInput="rgba(16,22,28,0.16)";

 return <div className={`${inter.className} flex h-dvh flex-col overflow-hidden bg-[#ECEEF0] text-[#10161C]`}>

  {/* BARRE DE STATUT */}
  <div className="flex flex-shrink-0 items-center justify-between border-b bg-white px-7 py-3.5" style={{borderColor:border}}>
   <div className="flex items-center gap-3">
    <span aria-hidden="true" className="grid h-8 w-8 place-items-center rounded-[9px]" style={{background:accent}}>
     <svg width="20" height="20" viewBox="0 0 40 40" fill="none"><path d="M9 22l4-9h5l2 5 2-5h5l4 9" stroke="white" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round"/><circle cx="14" cy="27" r="2.4" stroke="white" strokeWidth="1.8"/><circle cx="26" cy="27" r="2.4" stroke="white" strokeWidth="1.8"/></svg>
    </span>
    <div>
     <div className="text-[15px] font-extrabold tracking-tight">DiagPilot</div>
     <div className="text-[10.5px] font-semibold" style={{color:"rgba(16,22,28,0.42)"}}>Terminal atelier</div>
    </div>
   </div>
   <div className="flex items-center gap-2.5 rounded-lg px-3.5 py-2" style={{background:"rgba(16,22,28,0.05)"}}>
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><rect x="1.5" y="4" width="10.5" height="7" rx="1.5" stroke="rgba(16,22,28,0.5)" strokeWidth="1.3"/><path d="M12 6v3" stroke="rgba(16,22,28,0.5)" strokeWidth="1.3" strokeLinecap="round"/></svg>
    <span className="text-[12.5px] font-semibold" style={{color:"rgba(16,22,28,0.55)"}}>Tablette OBD</span>
   </div>
  </div>

  {/* BANDEAU MODE DÉMO */}
  <div className="flex flex-shrink-0 items-center justify-center gap-2.5 bg-[#10161C] px-7 py-2">
   <span className="text-[11px] font-bold uppercase tracking-[.08em] text-[#ECEEF0]" style={mono}>Mode démonstration</span>
   <span className="text-[11.5px]" style={{color:"rgba(236,238,240,0.55)"}}>données non contractuelles · aucune commande de calculateur</span>
  </div>

  {/* STEPPER */}
  <div className="flex flex-shrink-0 border-b bg-white" style={{borderColor:border}}>
   {labels.map((label,i)=>{const n=i+1;const done=n<step;const active=n===step;return (
    <div key={label} onClick={()=>goToStep(n)} className="flex flex-1 cursor-pointer flex-col items-center gap-2 border-b-[3px] px-2 pb-3.5 pt-4" style={{borderBottomColor:active?accent:"transparent"}}>
     <div className="flex items-center gap-2.5">
      <span className="grid h-[26px] w-[26px] shrink-0 place-items-center rounded-md text-[12.5px] font-extrabold" style={{...mono,background:done||active?accent:"rgba(16,22,28,0.07)",color:done||active?"#fff":"rgba(16,22,28,0.4)"}}>
       {done?<svg width="13" height="13" viewBox="0 0 13 13" fill="none"><path d="M2 6.5l3 3 6-6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>:n}
      </span>
      <span className="text-[13.5px]" style={{fontWeight:active?700:500,color:active?"#10161C":done?"rgba(16,22,28,0.55)":"rgba(16,22,28,0.4)"}}>{label}</span>
     </div>
    </div>
   )})}
  </div>

  {/* CONTENU */}
  <div className="flex flex-1 justify-center overflow-y-auto px-7 py-9">
   <div className="flex w-full max-w-[760px] flex-col gap-6">

    <div>
     <div className="mb-2 text-[11.5px] font-bold uppercase tracking-[.09em]" style={{...mono,color:accent}}>Diagnostic assisté par IA</div>
     <h1 className="mb-2 text-[26px] font-extrabold tracking-tight">Nouveau diagnostic</h1>
     <p className="max-w-[600px] text-[14.5px] leading-[1.65]" style={{color:"rgba(16,22,28,0.56)"}}>Croisez codes défauts, configuration véhicule, mesures et photos. L’assistant propose des contrôles, jamais un verdict automatique.</p>
    </div>

    {error&&<div role="alert" className="rounded-[10px] border border-red-300 bg-red-50 p-4 text-red-800">{error}</div>}

    <div className="rounded-xl border bg-white px-[30px] py-7" style={{borderColor:border}}>

     {step===1&&<div>
      <span className="mb-2.5 inline-block rounded-md px-2.5 py-1 text-[10.5px] font-bold uppercase tracking-[.06em]" style={{...mono,background:"rgba(16,22,28,0.06)",color:"rgba(16,22,28,0.5)"}}>Étape 1 obligatoire</span>
      <h2 className="mb-2 text-[19px] font-extrabold tracking-tight">Identifier le véhicule</h2>
      <p className="mb-[22px] max-w-[560px] text-[13.5px] leading-[1.6]" style={{color:"rgba(16,22,28,0.56)"}}>La plaque ou le VIN servent de clé. Vous confirmez toujours la motorisation et la transmission avant le diagnostic.</p>

      <div className="mb-[22px] inline-flex gap-0.5 rounded-[10px] p-1" style={{background:"rgba(16,22,28,0.05)"}}>
       <button type="button" onClick={()=>setIdentifierMode("registration")} className="rounded-lg px-5 py-3 text-[13.5px] font-bold" style={{background:identifierMode==="registration"?"#fff":"transparent",color:identifierMode==="registration"?accent:"rgba(16,22,28,0.5)"}}>Plaque</button>
       <button type="button" onClick={()=>setIdentifierMode("vin")} className="rounded-lg px-5 py-3 text-[13.5px] font-bold" style={{background:identifierMode==="vin"?"#fff":"transparent",color:identifierMode==="vin"?accent:"rgba(16,22,28,0.5)"}}>VIN</button>
      </div>

      <form onSubmit={identify}>
       {identifierMode==="registration"?<div className="mb-5 flex gap-3.5">
        <div className="flex-[2]">
         <label className="mb-1.5 block text-[12px] font-bold" style={{color:"rgba(16,22,28,0.62)"}}>Plaque d’immatriculation *</label>
         <input required value={registration} onChange={e=>setRegistration(e.target.value)} placeholder="AA-123-BB" className="box-border h-[50px] w-full rounded-[10px] border bg-white px-4 text-[16px] font-bold uppercase" style={{...mono,borderColor:borderInput}}/>
        </div>
        <div className="flex-1">
         <label className="mb-1.5 block text-[12px] font-bold" style={{color:"rgba(16,22,28,0.62)"}}>Pays</label>
         <select value={country} onChange={e=>setCountry(e.target.value)} className="box-border h-[50px] w-full appearance-none rounded-[10px] border bg-white px-4 text-[14px] font-semibold" style={{borderColor:borderInput}}>
          <option value="FR">France</option><option value="BE">Belgique</option><option value="CH">Suisse</option><option value="LU">Luxembourg</option>
         </select>
        </div>
       </div>:<div className="mb-5">
        <label className="mb-1.5 block text-[12px] font-bold" style={{color:"rgba(16,22,28,0.62)"}}>Numéro de châssis (VIN) *</label>
        <input required minLength={11} maxLength={17} value={vin} onChange={e=>setVin(e.target.value)} placeholder="VF1XXXXXXXXXXXXXX" className="box-border h-[50px] w-full rounded-[10px] border bg-white px-4 text-[16px] font-bold uppercase" style={{...mono,borderColor:borderInput}}/>
        <p className="mt-2 text-[12px]" style={{color:"rgba(16,22,28,0.45)"}}>Le VIN complet est chiffré côté serveur et n’est jamais affiché dans les journaux.</p>
       </div>}
       <div className="flex flex-wrap items-center gap-3.5">
        <button className="min-h-[48px] rounded-[10px] px-[26px] py-3.5 text-[14px] font-bold text-white" style={{background:accent}} disabled={busy||(identifierMode==="registration"?registration.trim().length<4:vin.trim().length<11)}>{busy?"Identification…":"Rechercher"}</button>
        {identifierMode==="registration"&&<span className="text-[12px]" style={{color:"rgba(16,22,28,0.45)"}}>Mode démonstration : <button type="button" className="font-bold underline" style={{color:"rgba(16,22,28,0.65)"}} onClick={()=>setRegistration("DEMO123")}>utiliser DEMO123</button></span>}
       </div>
      </form>

      {lookup?.candidates?.length?<div className="mt-6 rounded-[10px] border p-4" style={{borderColor:"rgba(51,73,92,0.25)",background:"rgba(51,73,92,0.05)"}}>
       <h3 className="font-bold">Configurations trouvées</h3>
       <p className="mt-1 text-[13px]" style={{color:"rgba(16,22,28,0.56)"}}>Sélectionnez la version en vérifiant les éléments distinctifs.</p>
       <div className="mt-3 space-y-3">{lookup.candidates.map(c=><label key={c.id} className="flex cursor-pointer gap-3 rounded-[10px] border bg-white p-4" style={{borderColor:border}}>
        <input type="radio" name="candidate" value={c.id} checked={candidateId===c.id&&!manualOpen} onChange={()=>{setCandidateId(c.id);setManualOpen(false)}}/>
        <span><strong className="block">{c.make} {c.model} {c.generation} · {c.model_year??"année inconnue"}</strong>
         <span className="text-[13px]" style={{color:"rgba(16,22,28,0.56)"}}>{c.engine_name||c.engine_code||"moteur à confirmer"} · {c.engine_power_hp??(c.engine_power_kw?Math.round(c.engine_power_kw*1.36):"?")} ch · {c.transmission_type||"boîte à confirmer"} {c.transmission_gears?`${c.transmission_gears} rapports`:""}</span>
         <span className="mt-2 block text-[11px] font-semibold" style={{color:accent}}>Source : {c.provider_name} · score indicatif {Math.round(c.confidence_score*100)}% · confirmation humaine requise</span>
        </span>
       </label>)}</div>
       <button type="button" className="mt-3 text-[13px] font-semibold underline" style={{color:accent}} onClick={()=>setManualOpen(true)}>Le moteur a été remplacé ou aucune variante ne correspond</button>
      </div>:null}

      {lookup?.resolution_id&&manualOpen?<fieldset className="mt-6 rounded-[10px] border p-4" style={{borderColor:"rgba(176,74,62,0.3)",background:"rgba(176,74,62,0.05)"}}>
       <legend className="px-2 font-bold">Identification manuelle confirmée par le garagiste</legend>
       <p className="mb-4 text-[13px]" style={{color:"rgba(16,22,28,0.56)"}}>Le code moteur est fortement recommandé et sera prioritaire pour l’analyse.</p>
       <div className="grid gap-4 md:grid-cols-3">{([['make','Marque *'],['model','Modèle *'],['generation','Génération'],['model_year','Année'],['engine_code','Code moteur *'],['engine_displacement_cc','Cylindrée (cm³)'],['engine_power_hp','Puissance (ch)'],['transmission_code','Code boîte'],['transmission_gears','Rapports'],['tecdoc_k_type','K-Type TecDoc'],['cnit','CNIT']] as [keyof ManualVehicle,string][]).map(([key,label])=><div key={key}>
        <label className="mb-1.5 block text-[12px] font-bold" style={{color:"rgba(16,22,28,0.62)"}}>{label}</label>
        <input className="box-border h-[46px] w-full rounded-[10px] border bg-white px-3.5 text-[14px]" style={{borderColor:borderInput}} type={['model_year','engine_displacement_cc','engine_power_hp','transmission_gears'].includes(key)?'number':'text'} value={manual[key]} onChange={e=>setManual({...manual,[key]:e.target.value})}/>
       </div>)}
       <div><label className="mb-1.5 block text-[12px] font-bold" style={{color:"rgba(16,22,28,0.62)"}}>Carburant</label><select className="box-border h-[46px] w-full rounded-[10px] border bg-white px-3.5 text-[14px]" style={{borderColor:borderInput}} value={manual.fuel_type} onChange={e=>setManual({...manual,fuel_type:e.target.value})}><option value="diesel">Diesel</option><option value="gasoline">Essence</option><option value="hybrid">Hybride</option><option value="electric">Électrique</option></select></div>
       <div><label className="mb-1.5 block text-[12px] font-bold" style={{color:"rgba(16,22,28,0.62)"}}>Type de boîte</label><select className="box-border h-[46px] w-full rounded-[10px] border bg-white px-3.5 text-[14px]" style={{borderColor:borderInput}} value={manual.transmission_type} onChange={e=>setManual({...manual,transmission_type:e.target.value})}><option value="manual">Manuelle</option><option value="automatic">Automatique</option><option value="robotized">Robotisée</option><option value="cvt">CVT</option></select></div>
       </div>
      </fieldset>:null}

      {lookup?.resolution_id?<button type="button" className="mt-5 min-h-[48px] rounded-[10px] px-[26px] py-3.5 text-[14px] font-bold text-white disabled:opacity-40" style={{background:accent}} disabled={busy||(!candidateId&&!manualOpen)} onClick={confirmVehicle}>{manualOpen?"Confirmer la saisie manuelle":"Confirmer ce véhicule"}</button>:null}
     </div>}

     {step===2&&<div>
      <h2 className="mb-2 text-[19px] font-extrabold tracking-tight">Codes défauts &amp; symptômes</h2>
      <p className="mb-5 max-w-[560px] text-[13.5px] leading-[1.6]" style={{color:"rgba(16,22,28,0.56)"}}>Renseignez les codes DTC lus au lecteur et décrivez, si utile, les symptômes observés.</p>

      <div className="mb-4 flex flex-wrap gap-3.5">
       <div><label className="mb-1.5 block text-[12px] font-bold" style={{color:"rgba(16,22,28,0.62)"}}>Kilométrage</label><input type="number" min="0" value={mileage} onChange={e=>setMileage(e.target.value)} className="box-border h-[46px] w-[160px] rounded-[10px] border bg-white px-3.5 text-[14px]" style={{...mono,borderColor:borderInput}}/></div>
       <div><label className="mb-1.5 block text-[12px] font-bold" style={{color:"rgba(16,22,28,0.62)"}}>Calculateur</label><input value={ecu} onChange={e=>setEcu(e.target.value)} className="box-border h-[46px] w-[200px] rounded-[10px] border bg-white px-3.5 text-[14px]" style={{borderColor:borderInput}}/></div>
       <div><label className="mb-1.5 block text-[12px] font-bold" style={{color:"rgba(16,22,28,0.62)"}}>Statut</label><select value={status} onChange={e=>setStatus(e.target.value)} className="box-border h-[46px] w-[160px] appearance-none rounded-[10px] border bg-white px-3.5 text-[14px]" style={{borderColor:borderInput}}><option value="active">Actif</option><option value="intermittent">Intermittent</option><option value="stored">Mémorisé</option><option value="unknown">Inconnu</option></select></div>
      </div>

      <div className="mb-4 flex gap-2.5">
       <input value={codes} onChange={e=>setCodes(e.target.value)} placeholder="Ex. P0301" className="max-w-[220px] flex-1 rounded-[10px] border bg-white px-4 py-3.5 text-[14px] font-bold uppercase" style={{...mono,borderColor:borderInput}}/>
      </div>
      <p className="mb-4 text-[12px]" style={{color:"rgba(16,22,28,0.45)"}}>Séparez les codes par une virgule, un espace ou une ligne.</p>

      <div className="mb-[22px] flex flex-wrap gap-2.5">{parsedCodes.map(code=><div key={code} className="flex items-center gap-2 rounded-[10px] border py-2.5 pl-4 pr-2.5" style={{background:"rgba(16,22,28,0.05)",borderColor:border}}>
       <span className="text-[13px] font-extrabold" style={mono}>{code}</span>
      </div>)}</div>

      <label className="mb-1.5 block text-[12px] font-bold" style={{color:"rgba(16,22,28,0.62)"}}>Symptômes observés (optionnel)</label>
      <textarea value={symptoms} onChange={e=>setSymptoms(e.target.value)} placeholder="Facultatif : le catalogue de 65 536 codes permet déjà une première analyse à partir du seul code." className="min-h-[96px] w-full resize-y rounded-[10px] border bg-white px-4 py-3.5 text-[14px]" style={{borderColor:borderInput}}/>
      <label className="mb-1.5 mt-4 block text-[12px] font-bold" style={{color:"rgba(16,22,28,0.62)"}}>Circonstances d’apparition (optionnel)</label>
      <textarea value={circumstances} onChange={e=>setCircumstances(e.target.value)} className="min-h-[80px] w-full resize-y rounded-[10px] border bg-white px-4 py-3.5 text-[14px]" style={{borderColor:borderInput}}/>
     </div>}

     {step===3&&<div>
      <h2 className="mb-2 text-[19px] font-extrabold tracking-tight">Preuves &amp; mesures</h2>
      <p className="mb-5 max-w-[560px] text-[13.5px] leading-[1.6]" style={{color:"rgba(16,22,28,0.56)"}}>Ajoutez vos relevés terrain et jusqu’à huit photos (connecteurs, faisceaux, pièces suspectées). Étape facultative mais recommandée.</p>

      <label className="mb-2 block text-[11.5px] font-bold" style={{color:"rgba(16,22,28,0.55)"}}>Mesure manuelle</label>
      <div className="mb-3 grid gap-3.5 md:grid-cols-4">
       <input placeholder="Nom (ex. Pression rail)" value={measure.name} onChange={e=>setMeasure({...measure,name:e.target.value})} className="rounded-[10px] border bg-white px-3.5 py-3 text-[14px]" style={{borderColor:borderInput}}/>
       <div className="flex items-center overflow-hidden rounded-[10px] border bg-white" style={{borderColor:borderInput}}>
        <input placeholder="250" value={measure.value} onChange={e=>setMeasure({...measure,value:e.target.value})} className="min-w-0 flex-1 border-none bg-transparent px-3.5 py-3 text-[14px] font-bold" style={mono}/>
        <input placeholder="bar" value={measure.unit} onChange={e=>setMeasure({...measure,unit:e.target.value})} className="w-[70px] border-none bg-transparent px-3 py-3 text-right text-[11.5px] font-bold" style={{color:"rgba(16,22,28,0.4)"}}/>
       </div>
       <button type="button" onClick={addMeasurement} className="rounded-[10px] px-4 py-3 text-[13.5px] font-bold" style={{background:"rgba(51,73,92,0.10)",color:accent}}>+ Ajouter</button>
      </div>
      {measurements.length?<ul className="mb-[26px] space-y-2">{measurements.map((m,i)=><li key={`${m.name}-${i}`} className="flex items-center justify-between rounded-[10px] px-4 py-3" style={{background:"rgba(16,22,28,0.03)"}}>
       <span className="text-[13.5px]">{m.name} : <strong style={mono}>{m.value} {m.unit}</strong></span>
       <button type="button" className="text-[12px] font-semibold text-red-700" onClick={()=>setMeasurements(x=>x.filter((_,j)=>j!==i))}>Retirer</button>
      </li>)}</ul>:<div className="mb-[26px]"/>}

      <label className="mb-3 block text-[12px] font-bold" style={{color:"rgba(16,22,28,0.62)"}}>Photos (8 max)</label>
      <input id="images" className="sr-only" type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={e=>e.target.files&&addImages(e.target.files)}/>
      <div className="grid grid-cols-4 gap-3">{Array.from({length:8}).map((_,i)=>{const item=images[i];return item?
       <div key={item.preview} className="relative aspect-square overflow-hidden rounded-[10px] border" style={{borderColor:border}}>
        <img src={item.preview} alt={`Aperçu ${item.file.name}`} className="h-full w-full object-cover"/>
        <button type="button" onClick={()=>removeImage(i)} className="absolute right-1.5 top-1.5 grid h-6 w-6 place-items-center rounded-md bg-black/60 text-xs text-white">✕</button>
       </div>
       :<label key={i} htmlFor="images" className="flex aspect-square min-h-[88px] cursor-pointer flex-col items-center justify-center gap-1.5 rounded-[10px] border-[1.5px] border-dashed" style={{borderColor:"rgba(16,22,28,0.22)",background:"rgba(16,22,28,0.02)"}}>
        <svg width="20" height="20" viewBox="0 0 17 17" fill="none"><rect x="2" y="4" width="13" height="10" rx="1.5" stroke="rgba(16,22,28,0.34)" strokeWidth="1.3"/><circle cx="6" cy="8" r="1.4" stroke="rgba(16,22,28,0.34)" strokeWidth="1.2"/><path d="M2 12l3.3-3.3 2.7 2.7L11 8l4 4" stroke="rgba(16,22,28,0.34)" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/></svg>
        <span className="text-[10.5px] font-bold" style={{color:"rgba(16,22,28,0.4)"}}>Photo {i+1}</span>
       </label>})}</div>

      {images.length?<div className="mt-5 space-y-3">{images.map((item,i)=><div key={item.preview} className="flex flex-wrap items-center gap-2.5 rounded-[10px] p-3" style={{background:"rgba(16,22,28,0.03)"}}>
       <strong className="max-w-[140px] truncate text-[12.5px]">{item.file.name}</strong>
       <select value={item.category} onChange={e=>setImages(x=>x.map((row,j)=>j===i?{...row,category:e.target.value}:row))} className="rounded-[8px] border bg-white px-2 py-1.5 text-[12.5px]" style={{borderColor:borderInput}}>
        <option value="engine_bay">Compartiment moteur</option><option value="dashboard">Tableau de bord</option><option value="diagnostic_tool">Outil diagnostic</option><option value="part_or_connector">Pièce ou connecteur</option><option value="leak">Fuite</option><option value="wear">Usure</option><option value="manufacturer_plate">Plaque constructeur</option><option value="other">Autre</option>
       </select>
       <input value={item.description} onChange={e=>setImages(x=>x.map((row,j)=>j===i?{...row,description:e.target.value}:row))} placeholder="Commentaire" className="min-w-[140px] flex-1 rounded-[8px] border bg-white px-2.5 py-1.5 text-[12.5px]" style={{borderColor:borderInput}}/>
      </div>)}</div>:null}
     </div>}

     {step===4&&<div>
      <h2 className="mb-2 text-[19px] font-extrabold tracking-tight">Validation avant analyse</h2>
      <p className="mb-5 max-w-[560px] text-[13.5px] leading-[1.6]" style={{color:"rgba(16,22,28,0.56)"}}>Vérifiez le récapitulatif ; les contrôles seront proposés par l’assistant juste après l’analyse.</p>

      <div className="mb-6 grid gap-3.5 md:grid-cols-2">
       <div className="rounded-[10px] border p-4" style={{background:"rgba(16,22,28,0.03)",borderColor:"rgba(16,22,28,0.07)"}}>
        <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-[.06em]" style={{color:"rgba(16,22,28,0.45)"}}>Véhicule</div>
        <div className="text-[14px] font-extrabold" style={mono}>{vehicle?.make} {vehicle?.model} · {vehicle?.engine_code}</div>
       </div>
       <div className="rounded-[10px] border p-4" style={{background:"rgba(16,22,28,0.03)",borderColor:"rgba(16,22,28,0.07)"}}>
        <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-[.06em]" style={{color:"rgba(16,22,28,0.45)"}}>Codes &amp; preuves</div>
        <div className="text-[14px] font-extrabold" style={mono}>{parsedCodes.length} code(s) · {measurements.length} mesure(s) · {images.length} photo(s)</div>
       </div>
       <div className="rounded-[10px] border p-4 md:col-span-2" style={{background:"rgba(16,22,28,0.03)",borderColor:"rgba(16,22,28,0.07)"}}>
        <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-[.06em]" style={{color:"rgba(16,22,28,0.45)"}}>Symptômes</div>
        <div className="text-[13.5px]">{symptoms.trim()||"Aucun renseigné — analyse basée sur le(s) code(s) et le véhicule"}</div>
        {busy&&images.length>0?<div className="mt-2 text-[12.5px] font-semibold" style={{color:accent}}>Upload : {uploadProgress}%</div>:null}
       </div>
      </div>

      <div className="flex items-start gap-2.5 rounded-[10px] border p-4" style={{background:"rgba(51,73,92,0.06)",borderColor:"rgba(51,73,92,0.18)"}}>
       <svg width="17" height="17" viewBox="0 0 16 16" fill="none" className="mt-0.5 shrink-0"><circle cx="8" cy="8" r="6.5" stroke={accent} strokeWidth="1.4"/><path d="M8 5v4M8 11h.01" stroke={accent} strokeWidth="1.4" strokeLinecap="round"/></svg>
       <span className="text-[12.5px] leading-[1.6]" style={{color:"#2a3d4d"}}>Aide à la décision uniquement — aucun remplacement de pièce ne doit être effectué sans contrôle de confirmation.</span>
      </div>
     </div>}

    </div>
   </div>
  </div>

  {/* BARRE D'ACTION */}
  <div className="flex flex-shrink-0 gap-3.5 border-t bg-white px-7 py-4" style={{borderColor:border}}>
   <button type="button" disabled={busy||step===1} onClick={()=>setStep(x=>Math.max(1,x-1))} className="min-h-[52px] flex-none basis-[180px] rounded-[10px] border px-5 py-3.5 text-[14.5px] font-bold disabled:opacity-40" style={{borderColor:"rgba(16,22,28,0.18)",color:"rgba(16,22,28,0.65)"}}>Retour</button>
   {step<4?<button type="button" disabled={busy||(step===1&&!vehicleId)} onClick={advance} className="min-h-[52px] flex-1 rounded-[10px] px-5 py-3.5 text-[14.5px] font-bold text-white disabled:opacity-40" style={{background:accent}}>Continuer</button>
   :<button type="button" disabled={busy} onClick={submit} className="min-h-[52px] flex-1 rounded-[10px] px-5 py-3.5 text-[14.5px] font-bold text-white disabled:opacity-40" style={{background:accent}}>{busy?"Analyse sécurisée en cours…":"Lancer l’analyse IA"}</button>}
  </div>
 </div>
}
