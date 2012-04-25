function change_icon(id) {
    var s = document.getElementById(id);
    if (s.which == "1") {
        s.src="img/plus.jpeg";
        s.which = "2";
    }else{
        s.src="img/minus.jpeg";
        s.which = "1";
    }
    isHidden('parameters')
}

function batch_input(oDiv){
    var vDiv = document.getElementById(oDiv);
    vDiv.style.display = (vDiv.style.display == 'none')?'block':'none';

    var input_table =document.getElementById("input_table");
    var input_table_length = input_table.rows.length;

    while (input_table_length > 2){
        input_table.deleteRow(input_table_length - 1);
	input_table_length = input_table.rows.length;
    }

    for (var i=1; i <= input_table_length; i++) {
        var seq_id = 'seq' + i + '_id';
        var seq_obj = document.getElementById(seq_id);
        seq_obj.value="";
    }
}

function isHidden(oDiv){
    var vDiv = document.getElementById(oDiv);
    vDiv.style.display = (vDiv.style.display == 'none')?'block':'none';
}

function clust_align(sn){
    var flag = 0
    for (var i=1; i <= sn; i++) {
        var check_desc_id = 'Amplicon_desc_' + i;
        var check_desc = document.getElementById(check_desc_id);

        if (check_desc.checked == true){
            flag++; 
        }
    }
    if (flag <= 1) {
        alert('Please select more than one amplicons for cluster and multiple alignment.')
    }else{
        document.output_form.action="clust_align";
        document.output_form.submit();
    }
}


function multi_align(sn){
    var flag = 0
    for (var i=1; i <= sn; i++) {
        var check_desc_id = 'Amplicon_desc_' + i;
        var check_desc = document.getElementById(check_desc_id);

        if (check_desc.checked == true){
            flag++; 
        }
    }
    if (flag <= 1) {
        alert('Please select more than one amplicons for multiple alignment.')
    }else{
        document.output_form.action="multi_align";
        document.output_form.submit();
    }
}

function export_amplicon(sn){
    var flag = 0
    for (var i=1; i <= sn; i++) {
        var check_desc_id = 'Amplicon_desc_' + i;
        var check_desc = document.getElementById(check_desc_id);

        if (check_desc.checked == true){
            flag++; 
        }
    }
    if (flag <= 0) {
        alert('Please select amplicon(s) for exporting.')
    }else{
	the_form = document.getElementById("output_form");
	the_form.action="export_to_fasta";
	the_form.submit();
    }
}

function virtual_e(sn){
    var flag = 0
    for (var i=1; i <= sn; i++) {
        var check_desc_id = 'Amplicon_desc_' + i;
        var check_desc = document.getElementById(check_desc_id);

        if (check_desc.checked == true){
            flag++; 
        }
    }
    if (flag <= 0) {
        alert('Please select amplicon(s) for Virtual Electrophoresis.')
    }else{
	the_form = document.getElementById("output_form");
	the_form.action="virtual_e";
	the_form.submit();
    }
}

function view_dimer(){
    the_form = document.getElementById("output_form");
    the_form.action="view_dimer";
    the_form.submit();
}

function check_all_db(){
    var ref_element = document.getElementById('all_db_checked_id');
    var db_list = document.getElementsByName('db_selected');
    for (var i=0; i < db_list.length; i++) {
	db_list[i].checked = ref_element.checked;
    }
}

function check_all(sn){
    var ref_element = document.getElementById('check_all_id')
    for (var i=1; i <= sn; i++) {
        var check_desc_id = 'Amplicon_desc_' + i;
        var check_desc = document.getElementById(check_desc_id);
        var check_detail_id = 'Amplicon_detail_' + i;
        var check_detail = document.getElementById(check_detail_id);

        check_desc.checked = ref_element.checked;
        check_detail.checked = ref_element.checked;
    }
}

function detail2desc_AssociationCheck(sn) {
    var ref_element = document.getElementById('check_all_id')
    var check_desc_id = 'Amplicon_desc_' + sn;
    var check_desc = document.getElementById(check_desc_id);
    var check_detail_id = 'Amplicon_detail_' + sn;
    var check_detail = document.getElementById(check_detail_id);

    if (check_desc.checked == true) {
        check_desc.checked = false;
        check_detail.checked = false;
    }else{
        check_desc.checked = true;
        check_detail.checked = true;
    }

}

function desc2detail_AssociationCheck(sn) {
    var check_desc_id = 'Amplicon_desc_' + sn;
    var check_desc = document.getElementById(check_desc_id);
    var check_detail_id = 'Amplicon_detail_' + sn;
    var check_detail = document.getElementById(check_detail_id);

    if (check_detail.checked == true) {
        check_desc.checked = false;
        check_detail.checked = false;
    }else{
        check_desc.checked = true;
        check_detail.checked = true;
    }

}

function addLoadEvent(func) {
    var oldonload = window.onload;
    if (typeof window.onload != 'function') {
        window.onload = func;
    } else {
        window.onload = function() {
            oldonload();
            func();
        }
    }
}

function addClass(element,value) {
    if (!element.className) {
        element.className = value;
    } else {
        newClassName = element.className;
        newClassName+= " ";
        newClassName+= value;
        element.className = newClassName;
    }
}


function stripeTables() {
    var tables = document.getElementsByTagName("table");
    for (var m=0; m<tables.length; m++) {
        if (tables[m].className == "list_table") {
            var tbodies = tables[m].getElementsByTagName("tbody");
            for (var i=0; i<tbodies.length; i++) {
                var odd = true;
                var rows = tbodies[i].getElementsByTagName("tr");
                for (var j=0; j<rows.length; j++) {
                    if (odd == false) {
                        odd = true;
                    } else {
                        addClass(rows[j],"odd");
                        odd = false;
                    }
                }
            }
        }
    }
}
function highlightRows() {
    if(!document.getElementsByTagName) return false;
    var tables = document.getElementsByTagName("table");
    for (var m=0; m<tables.length; m++) {
        if (tables[m].className == "list_table") {
            var tbodies = tables[m].getElementsByTagName("tbody");
            for (var j=0; j<tbodies.length; j++) {
                var rows = tbodies[j].getElementsByTagName("tr");
                for (var i=0; i<rows.length; i++) {
                    rows[i].oldClassName = rows[i].className
                    rows[i].onmouseover = function() {
                        if( this.className.indexOf("selected") == -1)
                        addClass(this,"highlight");
                    }
                    rows[i].onmouseout = function() {
                        if( this.className.indexOf("selected") == -1)
                        this.className = this.oldClassName
                    }
                }
            }
        }
    }
}

function selectCheckbox(checkbox) {
    var name = checkbox.name;
    var sn = name.split('_')[3];

    var check_detail_id = 'Amplicon_detail_' + sn;
    var check_detail = document.getElementById(check_detail_id);

    if (check_detail.checked == true) {
        checkbox.checked = false;
        check_detail.checked = false;
    } else {
        checkbox.checked = true;
        check_detail.checked = true;
    }
}

function selectRowCheckbox(row) {
    var checkbox = row.getElementsByTagName("input")[0];
    if (typeof(checkbox) != 'undefined'){
	var name = checkbox.name;
	var sn = name.split('_')[3];

	var check_detail_id = 'Amplicon_detail_' + sn;
	var check_detail = document.getElementById(check_detail_id);

	if (checkbox.checked == true) {
	    checkbox.checked = false;
	    check_detail.checked = false;
	} else {
	    checkbox.checked = true;
	    check_detail.checked = true;
	}
    }
}

function lockRow() {
    var tables = document.getElementsByTagName("table");
    for (var m=0; m<tables.length; m++) {
        if (tables[m].className == "list_table") {
            var tbodies = tables[m].getElementsByTagName("tbody");
            for (var j=0; j<tbodies.length; j++) {
                var rows = tbodies[j].getElementsByTagName("tr");
                for (var i=0; i<rows.length; i++) {
                    rows[i].oldClassName = rows[i].className;
                    rows[i].onclick = function() {
                        if (this.className.indexOf("selected") != -1) {
                            this.className = this.oldClassName;
                        } else {
                            // addClass(this,"selected");
                        }
                        selectRowCheckbox(this);
                    }
                }
            }
        }
    }
}

addLoadEvent(stripeTables);
addLoadEvent(highlightRows);
addLoadEvent(lockRow);


function lockRowUsingCheckbox() {
    var tables = document.getElementsByTagName("table");
    for (var m=0; m<tables.length; m++) {
        if (tables[m].className == "list_table") {
            var tbodies = tables[m].getElementsByTagName("tbody");
            for (var j=0; j<tbodies.length; j++) {
                var checkboxes = tbodies[j].getElementsByTagName("input");
                for (var i=0; i<checkboxes.length; i++) {
                    checkboxes[i].onclick = function(evt) {
                        if (this.parentNode.parentNode.className.indexOf("selected") != -1){
                            this.parentNode.parentNode.className = this.parentNode.parentNode.oldClassName;
                        } else {
                            // addClass(this.parentNode.parentNode,"selected");
                        }
                        if (window.event && !window.event.cancelBubble) {
                            window.event.cancelBubble = "true";
                        } else {
                            evt.stopPropagation();
                        }
                        selectCheckbox(this);
                    }
                }
            }
        }
    }
}
addLoadEvent(lockRowUsingCheckbox);

function upload_seq_changed(){
    var fasta_seq =document.getElementById("fasta_seq");
    fasta_seq.value = '';
}

function custom_db_changed(){
    var db_selected = document.main_form.db_selected;
    db_selected.selectedIndex = 0;
}


function return_home(){
    window.location = './batch';
}

function clear_current(sn){
    var seq_name = 'seq' + sn + '_id'
    var seq_obj = document.getElementById(seq_name);

    seq_obj.value="";
}

function clear(){
    var input_table =document.getElementById("input_table");
    var input_table_length = input_table.rows.length;
    for (var i=1; i <= input_table_length; i++) {
        var seq_id = 'seq' + i + '_id';
        var seq_obj = document.getElementById(seq_id);
        seq_obj.value="";

    }
    document.main_form.fasta_seq.value="";
}

function add_row(){
    var input_table =document.getElementById("input_table");
    var new_tr = input_table.insertRow(-1);
    var new_td0 = new_tr.insertCell(0);
    var new_td1 = new_tr.insertCell(1);
    var primer_num = input_table.rows.length;
    new_td0.innerHTML = '<label>Sequence ' + primer_num + ': </label><input class="seq_input" type="text" alt="Enter the primer sequence" id="seq' + primer_num + '_id" name="seq' + primer_num + '" >';
    new_td1.innerHTML = '<a href="javaScript:clear_current(' + primer_num + ')" name="clear">Clear</a>';
    new_td1.setAttribute("align", "right");
}

function del_row(){
    var input_table =document.getElementById("input_table");
    var input_table_length = input_table.rows.length;
    if (input_table_length >= 3){
        input_table.deleteRow(input_table_length - 1);
    }
}

function fillPrimer() {
    seq_array = new Array();
    seq_array[0] = "5'-TCAGCTGCCACGTCGACAACA-3'";    
    seq_array[1] = "5'-TGTGTGCAGCTGCTGGTGGC-3'";    
    //seq_array[2] = "ACGGAAGATGGACGGCCCGA";    
    //seq_array[3] = "5'-GGAGCACGCAGAGGTGGAAGC-3'";    

    var input_table =document.getElementById("input_table");
    var tb_length = input_table.rows.length;
    if (tb_length < 2){
	while (tb_length < 2){
	    add_row();
	    tb_length = input_table.rows.length;
	}
    }

    for (var i=1; i <= seq_array.length; i++) {
        var seq_id = 'seq' + i + '_id';
        var seq_obj = document.getElementById(seq_id);
        seq_obj.value=seq_array[i-1];
    }

    var upload_seq =document.getElementById("uploada_seq");
    refresh_upload(upload_seq);
}
function fillFastaSeq() {
    var fasta_seq =document.getElementById("fasta_seq");
    fasta_seq.value = ">Seq1\nTCAGCTGCCACGTCGACAACA\n>Seq2\nTGTGTGCAGCTGCTGGTGGC\n>Seq3\nACGGAAGATGGACGGCCCGA\n>Seq4\nGGAGCACGCAGAGGTGGAAGC";
    var upload_seq =document.getElementById("uploada_seq");
    refresh_upload(upload_seq);
}

function refresh_upload(who){
    var who_tmp = who.cloneNode(false);
    who_tmp.onchange = who.onchange;
    who.parentNode.replaceChild(who_tmp, who);
}


function fill_size_list() {
    var seq_obj = document.getElementById("size_list_id");
    seq_obj.value="100, 200, 300, 400, 500";
}
