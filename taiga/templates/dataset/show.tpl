{% extends "base.tpl" %}

{% macro download_link(format) -%}
  <a href="/rest/v0/datasets/{{meta.dataset_id}}?format={{ format }}">{{ format }}</a>
{%- endmacro %}

{% block title %}Dataset{% endblock %}
{% block content %}
  <h1>
    Name: 
    <a href="#" id="name" data-name="name" data-type="text" data-pk="{{ meta.dataset_id }}" 
    data-url="/dataset/update" data-title="Enter name">{{ meta.name }}</a>
  </h1>
  <p> 
    {% with %}
      {% if meta.is_published %}
        {% set publish_text = "Published" %}
        {% set publish_class = "alert-info" %}
        {% set is_published_boolean = "True" %}
      {% else %}
        {% set publish_text = "Unpublished" %}
        {% set publish_class = "alert-danger" %}
        {% set is_published_boolean = "False" %}
      {% endif %}
      <span class="badge {{ publish_class }}"><a href="#" id="is_published" data-name="is_published" data-type="select" data-pk="{{ meta.dataset_id }}" 
    data-url="/dataset/update" data-title="Choose" data-value="{{is_published_boolean}}">{{ publish_text }}</a></span>
    {% endwith %}

Data type: <a href="#" id="data_type" data-name="data_type" data-type="select2" 
                  data-pk="{{ meta.dataset_id }}" data-url="/dataset/update" 
                  data-title="Enter data type" data-value="{{ meta.data_type }}">{{ meta.data_type }}</a>    
    Tags: <a href="#" id="tags" data-name="tags" data-type="select2" data-pk="{{meta.dataset_id}}" 
                   data-url="/dataset/update" data-title="Enter tags">{{ dataset_tags|join(', ') }}</a>
  </p>
  <p> 
    Uploaded by {{ meta.created_by }} on {{ meta.created_timestamp }}, 
    
    Versions: 
    {% for version in versions %} 
      {% if version.version == meta.version %}
        <strong>v{{meta.version}}</strong>
      {% else %}
        <a href="/dataset/show/{{ version.dataset_id }}">v{{ version.version }}</a>
      {% endif %}
    {% endfor %}
    
    
  </p>
  <p>
  </p> 
  {% if meta.hdf5_path %}  
    <p> <a href="/upload/tabular-form?dataset_id={{meta.dataset_id}}">Upload a new version</a> </p>
  {% else %}
    <p> <a href="/upload/columnar-form?dataset_id={{meta.dataset_id}}">Upload a new version</a> </p>
  {% endif %}

  <h3>Download</h3>
  <p> You can use the following links to download this dataset as the following formats:
    {% for format in formats %}
      {% if not loop.first %}
        |
      {% endif %}
      {{ download_link(format) }}
    {% endfor %}
  </p>
  
  <h3>Description:</h3>
  <div class="well"><a href="#" id="description" data-name="description" data-type="textarea" data-pk="{{ meta.dataset_id }}" data-url="/dataset/update" data-title="Enter description">{{ meta.description }}</a></div>
  
  {% if dims %}
    <h3>Dimensions</h3>
  
    <table class="table table-bordered table-striped">
      <thead>
        <tr>
            <th></th>
            <th>Description</th>
            <th>Values</th>
        </tr>
      </thead>
    
      <tbody>
        {% for dim in dims %}
          <tr>
            <td>{{ loop.index }}</td>
            <td>{{ dim.name }}</td>
            <td>{{ dim.value_count }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  {% endif %}

  {% if "rdata" in formats %}
    <h3>Retrieving this dataset within R</h3>
    <p>
      You can fetch this dataset by its ID, and load it into your R session with code below.  Executing the following will load the matrix into your workspace with the name "data": 
      <pre>load(url("{{root_url}}/rest/v0/datasets/{{meta.dataset_id}}?format=rdata"));</pre>

      Fetching the data by it's ID will guarentee you get the same data each and every time this is executed.  Alternatively, you can fetch this data by its name, in in which case, you'll receive the latest version of the data.  Code for fetching by name, is as follows:
      <pre>load(url("{{root_url}}/rest/v0/namedDataset?fetch=content&format=rdata&name={{meta.name|urlencode}}"));</pre>
    </p>
  {% endif %}

{% endblock %}

{% block scripts %}
<script>
  $.fn.editable.defaults.mode = 'inline';
  $(document).ready(function() {
    
    $('.x-editable-class').editable();

    $('#name').editable();

    $('#description').editable({
      inputclass: 'input-large',
    });
    
    $('#tags').editable({
      inputclass: 'input-large',
      select2: {
          tags: {{ all_tags_as_json }},
          tokenSeparators: [",", " "]
      }
    });
    
    var autocomplete_if_in_list = function(values) { 
      return function (query){
        var data = {results: []};

        $.each(values, function(){
            if(query.term.length == 0 || this.toUpperCase().indexOf(query.term.toUpperCase()) >= 0 ){
                data.results.push({id: this, text: this });
            }
        });

        if(data.results.length == 0) {
          data.results.push({id: query.term, text: query.term})
        }

        query.callback(data);
      };
    }

    var existing_data_types = {{ existing_data_types }}
    $('#data_type').editable({
      select2: {
        width: 200,
        inputclass: 'input-large',
        query: autocomplete_if_in_list(existing_data_types)
      },
      display: function (value)
      {
          if (!value) {
              $(this).empty();
              return;
          }
          $(this).text(value);
      },
    });
    
    $('#is_published').editable({
      source: [
        {value: "True", text: 'Published'},
        {value: "False", text: 'Unpublished'}
    ],
    /*
            display: function(value, sourceData) {
                 var colors = {"": "gray", 1: "green", 2: "blue"},
                     elem = $.grep(sourceData, function(o){return o.value == value;});
                 
                 if(elem.length) {    
                     $(this).text(elem[0].text).css("color", colors[value]); 
                 } else {
                     $(this).empty(); 
                 }
            }   */
        });    
    
  });
</script>
{% endblock %}