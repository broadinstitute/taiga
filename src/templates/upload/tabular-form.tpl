{% extends "base.tpl" %}
{% block title %}Upload Tabular File{% endblock %}
{% block content %}

  <h1>Upload CSV as a new
    {% if new_version %} 
      Version of an existing Dataset
    {% else %}
      Dataset
    {% endif %}
  </h1>

  <p>
    This form can be used to create a new dataset from a tab-delimited text file.   The file is assumed to be a matrix of values with a header row and a header column that label the rows and columns respectively.  All other cells in the files must be numeric values.   The only exception to numeric values is "NA" can be used to indicate the value is missing.
  </p>

  <form class="form-horizontal" role="form" method="post" action="/upload/tabular" enctype="multipart/form-data">
    {% if new_version %} 
      <input type="hidden" name="overwrite_existing" value="true">
      <input type="hidden" name="name" value="{{name}}">
      <input type="hidden" name="overwrite_existing" value="true">
    {% endif %}
    <div class="form-group">
      <label for="inputName" class="col-sm-2 control-label">Dataset Name</label>
      <div class="col-sm-10">
        {% if new_version %}
          <input type="text" disabled value="{{name}}" class="form-control" id="inputName" placeholder="Name">
        {% else %}
          <input type="text" class="form-control" id="inputName" placeholder="Name" name="name">
        {% endif %}
      </div>
    </div>
    
    <div class="form-group">
      <label for="publishState" class="col-sm-2 control-label">Publish status</label>
      <div class="col-sm-2">
        <select class="form-control" id="publishedState" name="is_published">
          <option selected value="False">Unpublished</option>
          <option value="True">Published</option>
        </select>
      </div>
    </div>

    <div class="form-group">
      <label for="inputDataType" class="col-sm-2 control-label">Data type</label>
      <div class="controls col-sm-2">
        <input type="hidden" class="form-control select2" id="inputDataType" name="data_type"/>
      </div>
    </div>

    <div class="form-group">
      <label for="inputColumnValues" class="col-sm-2 control-label">Columns represent</label>
      <div class="col-sm-10">
        <input type="text" class="form-control" id="inputColumnValues" placeholder="The meaning of the column labels (Example: Cell line)" name="columns" value="{{columns}}">
      </div>
    </div>
    <div class="form-group">
      <label for="inputRowValues" class="col-sm-2 control-label">Rows represent</label>
      <div class="col-sm-10">
        <input type="text" class="form-control" id="inputRowValues" placeholder="The meaning of the row labels (Example: Gene)" name="rows" value="{{rows}}">
      </div>
    </div>
    <div class="form-group">
      <label for="inputDescription" class="col-sm-2 control-label">Description</label>
      <div class="col-sm-10">
        <textarea id="inputDescription" class="form-control" rows="3" name="description">{{description}}</textarea>
      </div>
    </div>
    <div class="form-group">
      <label for="inputFile" class="col-sm-2 control-label">File</label>
      <div class="col-sm-10">
        <input type="file" class="form-control" id="inputFile" name="file">
      </div>
    </div>
    <div class="form-group">
      <div class="col-sm-offset-2 col-sm-10">
        <button type="submit" class="btn btn-default">Submit</button>
      </div>
    </div>
  </form>

{% endblock %}

{% block scripts %}
<script>
$(document).ready(function () {
  
  var existing_data_types = {{ existing_data_types }}
  
  $('#inputDataType').select2({
    query: function (query){
          var data = {results: []};
 
          $.each(existing_data_types, function(){
              if(query.term.length == 0 || this.toUpperCase().indexOf(query.term.toUpperCase()) >= 0 ){
                  data.results.push({id: this, text: this });
              }
          });

          if(data.results.length == 0) {
            data.results.push({id: query.term, text: query.term})
          }

          query.callback(data);
      }
  });
});
</script>
{% endblock %}
