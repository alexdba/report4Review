function CustomFormJS(targetId, formEmptyMessage, textYes, textNo, editMode, readOnly){
    this.controls = Array();
    this.formEmptyMessage = (formEmptyMessage ? formEmptyMessage : 'The form is empty');
    this.targetId = '#'+ (targetId ? targetId : 'target');
    this.canvas = this.targetId + ' > fieldset';
    this.trad = [(textYes?textYes:'Yes'), (textNo?textNo:'No')];
    this.editMode = editMode;
    this.readOnly = readOnly;

    this.load = function (controlData){
        this.controls = JSON.parse(controlData);
        this.renderControls();
    }

    this.createControl = function(id, d){
        checkMax = function(size){
            return (size?'onkeyup="javascript:if(this.value.length > '+size+') this.value = this.value.substring(0,'+size+')"':'')
        }
        limit = '';
        disabled = this.readOnly ? ' disabled ' : '';
        div = $('<div class="my-control" id="control-'+(id)+'"></div>');
        if(d.type=='textarea'){
            c = $('<textarea '+checkMax(d.max)+disabled+'></textarea>').
            attr('id', 'control-content-'+id).
            attr('name', 'control-content-'+id).val(d.value);
            if(d.min || d.max)
                limit = ' (' + (d.min ? 'Min: ' + d.min : '') + (d.min ? ', ' : '') + (d.max ? 'Max: ' + d.max : '') + ')';
        }else if(d.type=='text'){
            c = $('<input type="text" '+checkMax(d.max)+disabled+'></input>')
            .attr('id', 'control-content-'+id)
            .attr('name', 'control-content-'+id).val(d.value);
            if(d.min || d.max)
                limit = ' (' + (d.min ? 'Min: ' + d.min : '') + (d.min ? ', ' : '') + (d.max ? 'Max: ' + d.max : '') + ')';
        }else if(d.type=='yesno'){
            c = new Array();
            div.css('padding-bottom', 10)
            var valor = ['yes','no'];
            for(i=0;i<valor.length;i++)
                c.push($('<label class="radio inline">'+
                         '<input type="radio" name="control-content-'+id+'" '+ disabled + (d.value==valor[i] ? 'checked' : '') +
                         ' id="control-content-'+id+'" value="'+valor[i]+'" />'+this.trad[i]+'</label>'));
        }else if(d.type=='scale'){
            c = new Array();
            div.css('padding-bottom', 10)
            for(i=d.min;i<=d.max;i++)
                c.push($('<label class="radio inline">'+
                         '<input type="radio" name="control-content-'+id+'"'+ disabled +
                         ' id="control-content-'+id+'" value="'+i+'" '+ (d.value==i ? 'checked' : '') +'/>'+i+'</label>'));
        }
        if(this.editMode){
            div.append($('<div class="btn-toolbar" style="float:right">').
                             append($('<div class="btn-group">').
                                    append($('<a class="btn btn-mini"">').
                                            append('<i class="icon-arrow-up">').
                                               bind('click', $.proxy( this.moveControl, this, id, true))).
                                    append($('<a class="btn btn-mini">').
                                            append('<i class="icon-arrow-down">').
                                               bind('click', $.proxy( this.moveControl, this, id, false))).
                                    append($('<a class="btn btn-mini">').
                                            append('<i class="icon-trash">').
                                               bind('click', $.proxy( this.removeControl, this, id)))
                                    )
                       );
        }
        div.append($('<label class="control-label">'+ (id+1) + '. ' + d.label + limit+'</label>'));
        if(d.desc) div.append($('<pre>'+d.desc+'</pre>'));
        div.append(c);
        div.append($('<hr></hr>'));
        $(this.canvas).append(div);
        return c;
    }

    this.addControl = function(type,label,desc,min,max,value){
        this.controls.push({'type':type,'label':label,'desc':desc,'min':min,'max':max,'value':value});
        this.renderControls();
    }

    this.renderControls = function(){
        $(this.canvas).children().remove();
        if(this.controls.length>0)
            for(id=0;id<this.controls.length;id++)
                this.createControl(id, this.controls[id]);
        else
            $(this.canvas).append($('<h2>'+this.formEmptyMessage+'</h2>'));
    }

    this.moveControl = function(id, up){
        //id = parseInt($(ref).parents('div .my-control').attr('id').split('-')[1]);
        var new_id = (up ? id-1 : id+1);
        if(new_id < 0 || new_id > (this.controls.length-1)) return;
        var temp =  this.controls[new_id];
        this.controls[new_id] = this.controls[id];
        this.controls[id] = temp;
        this.renderControls();
    }

    this.removeControl = function (id){
        if((id<0) && this.controls.length > 0){
            if(!window.confirm('Delete all items?')) return;
            this.controls = new Array();
        } else {
            if(!window.confirm('Delete item ' + (id+1) + ' ?')) return;
            this.controls.splice(id,1);
        }
        this.renderControls();
    }

    this.validateData = function(){
        controls=this.loadValues(true);
        var errors = [];
        $.each(controls, function (i,d) {
            if (['text','textarea'].indexOf(d.type) >= 0 && (d.value.length < d.min || (d.max && d.value.length > d.max))) errors.push(d);
            else if (['yesno','scale'].indexOf(d.type) >= 0 && !d.value) errors.push(d);
        });
        return errors;
    }

    this.loadValues = function (includeData){
        t=$(this.targetId);
        var values = t.serializeArray();
        controls=this.controls;
        $.each(t.serializeArray(), function (i,d) {
            controls[parseInt(d.name.split("-")[2])].value = includeData ? d.value : '';
        });
        return controls;
    }

    this.saveControls = function(includeData){
        return JSON.stringify(this.loadValues(includeData))
    }
}
