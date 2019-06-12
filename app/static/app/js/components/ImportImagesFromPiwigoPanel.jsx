import '../css/ImportTaskPanel.scss';
import React from 'react';
import PropTypes from 'prop-types';
import ErrorMessage from './ErrorMessage';
import Select from 'react-select';

class ImportImagesFromPiwigoPanel extends React.Component {
  static defaultProps = {
  };

  static propTypes = {
      onImported: PropTypes.func.isRequired,
      onCancel: PropTypes.func,
      projectId: PropTypes.number.isRequired
  };

  constructor(props){
    super(props);

    this.state = {
      error: "",
      options: [],
      loadingOptionsFromPiwigo: false,
      importingFromPiwigo: false,
      importUrl: ""
    };
    
    this.loadPiwigoAlbums();
  }

  defaultTaskName = () => {
    return `Task of ${new Date().toISOString()}`;
  }

  cancel = (e) => {
    this.props.onCancel();
  }
  
  handleChangeImportUrl = (e) => {
    this.setState({importUrl: e.value});
  }

  handleConfirmImportUrl = () => {
    this.setState({importingFromPiwigo: true});

    $.post(`/api/projects/${this.props.projectId}/tasks/importimages`,
      {
        url: this.state.importUrl,
        name: this.defaultTaskName()
      }
    ).done(json => {
      this.setState({importingFromPiwigo: false});

      if (json.id){
        this.props.onImported();
      }else{
        this.setState({error: json.error || `Cannot import from URL, server responded: ${JSON.stringify(json)}`});
      }
    })
    .fail(() => {
        this.setState({importingFromPiwigo: false, error: "Cannot import from URL. Check your internet connection."});
    });
  }

  loadPiwigoAlbums = () => {
    this.setState({loadingOptionsFromPiwigo: true});
    $.get(`/api/projects/${this.props.projectId}/tasks/albums`)
    .done(json => {
      this.setState({options: json});
    })
    .fail((error) => {
        this.setState({loadingOptionsFromPiwigo: false, error: "Cannot load albums from Piwigo. Check your internet connection."});
    });
  }

  render() {
    return (
      <div className="import-task-panel theme-background-highlight">
        <div className="form-horizontal">
          <ErrorMessage bind={[this, 'error']} />

          <button type="button" className="close theme-color-primary" aria-label="Close" onClick={this.cancel}><span aria-hidden="true">&times;</span></button>
          <h4>Import Images From Piwigo</h4>
          <p>You can import the images in a Piwigo album to use for a new task.</p>          
          
          <div className="form-inline">
            <div className="form-group">
              <div style={{width:600, display: 'inline-block'}}>
                <Select
                  className="basic-single"
                  classNamePrefix="select"
                  isDisabled={this.state.importingFromPiwigo}
                  isLoading={this.state.loadingOptionsFromPiwigo}
                  isClearable={false}
                  isSearchable={true}
                  onChange={this.handleChangeImportUrl}
                  options={this.state.options}
                  placeholder={this.state.loadingOptionsFromPiwigo ? "Fetching Piwigo albums..." : "Please select a Piwigo album"}
                  name="options"
                />
              </div>
              <button onClick={this.handleConfirmImportUrl}
                      disabled={this.state.importUrl.length < 4 || this.state.importingFromPiwigo} 
                      className="btn-import btn btn-primary"><i className="glyphicon glyphicon-cloud-download"></i> Import</button>
            </div>
          </div>
          <p><b>Note</b>: when importing an album, you only import the images inside. All the sub-albums are ignored. Also, there is a limit of 500 images uploaded per album.</p>
        </div>
      </div>
    );
  }
}

export default ImportImagesFromPiwigoPanel;
