
def handle_ajax_request(request, missione, tipo_spesa):
    updated_rows = []
    deleted_rows = []
    if request.content_type == "application/json" or request.content_type.startswith("application/json"):
        try:
            # Parsing dei dati JSON
            datas = json.loads(request.body).get('data', [])
            for form_data in datas:
                valori = {}
                spesa_id = None
                formset_prefix = None
                is_delete = False

                # Estrai i valori e identifica il prefisso del formset
                for key, value in form_data.items():
                    new_key = key.split('-')[-1]
                    if new_key == 'id':
                        spesa_id = value if value else None
                    elif new_key == 'DELETE':
                        is_delete = value == 'on' or value == 'true' or value == True
                    else:
                        valori[new_key] = value

                    # Determina il prefisso del formset (utile per associare file)
                    if not formset_prefix:
                        prefix_split = key.split('-')
                        if len(prefix_split) > 1:
                            formset_prefix = f"{prefix_split[0]}-{prefix_split[1]}-"

                # Eliminazione del record se DELETE è selezionato
                if is_delete and spesa_id:
                    try:
                        spesa = Spesa.objects.get(id=spesa_id)
                        spesa.delete()
                        # Aggiungi il record eliminato alla lista `deleted_rows`
                        deleted_rows.append({
                            "id": spesa_id,
                            "formset_prefix": formset_prefix
                        })
                        return JsonResponse({"message": "Dati eliminati correttamente", "deleted_rows": deleted_rows}, status=200)
                        #return redirect('RimborsiApp:missioneUpdatePageAfterDelete', id=missione.id ,altrespese_formset_deleted = True)
                        #return  missioneUpdatePageAfterDelete(request, missione.id, tipo_spesa)
                        #return redirect('RimborsiApp:missione', id=missione.id)

                    except Exception as e:
                        return HttpResponseBadRequest(f"Errore nel salvataggio della spesa: {str(e)}")
                    except Spesa.DoesNotExist:
                        # falso positivo, da gestire qua? se, è rimasto nel DOM ma non è nel DB
                        return HttpResponseBadRequest(f"Errore: Spesa con id {spesa_id} non trovato.")


                # Gestisci delete se presente altrimenti la rimuovi
                valori.pop('DELETE', None)
                #creazione o aggiornamento Spesa
                if spesa_id:
                    # Aggiorna l'oggetto esistente
                    spesa = Spesa.objects.get(id=spesa_id)
                    for field, value in valori.items():
                        # Evita di sovrascrivere img_scontrino altrimenti l'immagine precedente sarà persa
                        if field != 'img_scontrino':
                              setattr(spesa, field, value)

                else:
                    # Creazione di un nuovo oggetto Spesa (data, importo, valuta sono OBBLIGATORI)
                    required_fields = ['data', 'importo', 'valuta']
                    if [field for field in required_fields if field not in valori or not valori[field]]:            #if missing_field
                        return HttpResponseBadRequest(f"Errore: i seguenti campi sono obbligatori e mancanti o vuoti: {', '.join(required_fields)}")

                    if 'importo' in valori:         #se importo è presente, converti in float
                        try:
                            valori['importo'] = float(valori['importo']) if valori['importo'] else 0.0
                        except ValueError:
                            return HttpResponseBadRequest("Errore: il campo 'importo' deve essere un numero valido.")

                    try:
                        spesa = Spesa(**valori)
                        spesa.save()
                        spesa_id = spesa.id
                    except Exception as e:
                        return HttpResponseBadRequest(f"Errore nel salvataggio della spesa: {str(e)}")

                # Salvataggio dell'oggetto
                spesa.save()

                # Associazione alla missione
                SpesaMissione.objects.update_or_create(missione=missione, spesa=spesa, tipo=tipo_spesa)

            if tipo_spesa == 'ALTRO':
                updated_rows.append({'formset_prefix': formset_prefix, 'altro_id': spesa_id})
            elif tipo_spesa == 'CONVEGNO':
                updated_rows.append({'formset_prefix': formset_prefix, 'convegno_id': spesa_id})
            else:
                updated_rows.append({'formset_prefix': formset_prefix, 'pernottamento_id': spesa_id})

            return JsonResponse({"message": "Dati salvati correttamente", "updated_rows": updated_rows}, status=200)
            #--------

        except Spesa.DoesNotExist:
            return HttpResponseBadRequest("Errore: spesa non trovata.")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            return HttpResponseBadRequest(f"Errore nel parsing dei dati: {e}")
        except Exception as e:
            return HttpResponseBadRequest(f"Errore sconosciuto: {e}")
   #image sect